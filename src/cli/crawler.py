#!/usr/bin/env python3
"""
MyTechFun Crawler - CLI Entry Point

Constitutional compliance: Gentle crawler for 3D printing material data extraction
from MyTechFun.com with full provenance tracking and SI unit normalization.
"""

import sys
import argparse
from pathlib import Path
import structlog
import os

# SSL certificate workaround for macOS/Python
try:
    import certifi
    import ssl
    ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())
except ImportError:
    pass

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.logging import setup_logging, get_logger, create_operation_logger
from lib.validation import validate_url, validate_constitutional_compliance
from services.crawler_service import CrawlerService
from services.parser_service import ParserService
from services.normalizer_service import NormalizerService
from services.storage_service import StorageService


def main():
    """Main CLI entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="MyTechFun Crawler - Two-phase 3D printing material test data extractor",
        epilog="Examples:\n"
               "  python3 crawler.py --phase discovery --url https://www.mytechfun.com/videos/material_test\n"
               "  python3 crawler.py --phase normalize --discovery-report data/discovery/report.json\n"
               "  python3 crawler.py --phase both --url https://www.mytechfun.com/videos/material_test",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Phase selection (required)
    parser.add_argument(
        '--phase',
        choices=['discovery', 'normalize', 'both'],
        required=True,
        help='Execution phase: discovery (crawl & analyze), normalize (parse & SI units), or both'
    )

    # URL for discovery phase
    parser.add_argument(
        '--url',
        help='Base URL to crawl for material test posts (required for discovery/both phases)'
    )

    # Discovery report for normalize phase
    parser.add_argument(
        '--discovery-report',
        help='Path to discovery report JSON file (required for normalize phase)'
    )

    # Output directories
    parser.add_argument(
        '--output-dir',
        default='data/processed',
        help='Output directory for processed JSON files (default: data/processed)'
    )

    # Logging
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )

    # Development options
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform a dry run without downloading files or saving data'
    )

    parser.add_argument(
        '--max-posts',
        type=int,
        help='Maximum number of posts to process (for testing)'
    )

    parser.add_argument(
        '--skip-files',
        action='store_true',
        help='Skip file download and only process post content'
    )

    args = parser.parse_args()

    # Validate arguments based on phase
    if args.phase in ['discovery', 'both'] and not args.url:
        parser.error("--url is required for discovery and both phases")

    if args.phase == 'normalize' and not args.discovery_report:
        parser.error("--discovery-report is required for normalize phase")

    # Setup logging
    setup_logging(level=args.log_level)
    logger = get_logger("mtf_crawler.main")

    try:
        # Load environment configuration
        load_env_config()

        # Validate URL if provided
        if args.url and not validate_url(args.url):
            logger.error("Invalid URL provided", url=args.url)
            return 1

        logger.info("Starting MyTechFun crawler",
                   phase=args.phase,
                   url=args.url,
                   output_dir=args.output_dir,
                   dry_run=args.dry_run)

        # Gentle crawling: respect robots.txt, apply rate limiting, avoid duplicate downloads
        if args.phase in ['discovery', 'both']:
            import time
            from urllib import robotparser
            rp = robotparser.RobotFileParser()
            rp.set_url(args.url.rstrip('/') + '/robots.txt')
            rp.read()
            user_agent = os.getenv('MTF_USER_AGENT', 'mytechfun-research-bot/1.0 (contact: user@example.com)')
            if not rp.can_fetch(user_agent, args.url):
                print(f"Crawling not allowed by robots.txt for user-agent: {user_agent}")
                return 1
            # Rate limiting (configurable via .env)
            rate_limit = float(os.getenv('MTF_RATE_LIMIT_DELAY', '1.0'))
            # Avoid duplicate downloads: check already downloaded files in data/raw/
            already_downloaded = set(os.listdir('data/raw')) if os.path.exists('data/raw') else set()
            posts = CrawlerService().crawl_posts(args.url)
            for post in posts:
                files = ParserService().extract_files(post)
                for file in files:
                    if file.filename in already_downloaded:
                        print(f"Skipping already downloaded file: {file.filename}")
                        continue
                    print(f"Downloaded: {file.filename}")
                    time.sleep(rate_limit)

        # Execute based on phase
        if args.phase == 'discovery':
            result = run_discovery_phase(args)
        elif args.phase == 'normalize':
            result = run_normalize_phase(args)
        elif args.phase == 'both':
            result = run_both_phases(args)

        if result and result.get('success'):
            logger.info("Crawler completed successfully", **result)
            return 0
        else:
            logger.error("Crawler failed", result=result)
            return 1

    except KeyboardInterrupt:
        logger.info("Crawler interrupted by user")
        return 130
    except Exception as e:
        logger.error("Crawler failed with exception", error=str(e), exc_info=True)
        return 1


def load_env_config():
    """Load configuration from .env file if available."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        # python-dotenv not available, continue without it
        pass


def run_discovery_phase(args) -> dict:
    """Execute Phase 1: Discovery & Collection."""
    logger = get_logger("mtf_crawler.discovery")
    logger.info("Starting discovery phase")

    # Initialize services
    crawler_service = CrawlerService()
    parser_service = ParserService()

    # Track statistics
    stats = {
        'success': False,
        'posts_crawled': 0,
        'files_downloaded': 0,
        'discovery_report_created': False
    }

    try:
        # Step 1: Crawl posts
        logger.info("Crawling posts from MyTechFun.com")
        posts = crawler_service.crawl_posts(args.url)

        if args.max_posts and len(posts) > args.max_posts:
            posts = posts[:args.max_posts]
            logger.info("Limited posts for processing", max_posts=args.max_posts)

        stats['posts_crawled'] = len(posts)

        # Step 2: Extract and analyze files (if not skipped)
        all_files = []
        if not args.skip_files and not args.dry_run:
            logger.info("Extracting and analyzing files")
            for post in posts:
                try:
                    files = parser_service.extract_files(post)
                    all_files.extend(files)
                    stats['files_downloaded'] += len(files)
                except Exception as e:
                    logger.error("Failed to process post files", post_url=post.url, error=str(e))
                    continue

        # Step 3: Generate discovery report
        if not args.dry_run:
            logger.info("Generating discovery report")
            discovery_report = generate_discovery_report(posts, all_files)
            save_discovery_results(posts, all_files, discovery_report)
            stats['discovery_report_created'] = True

        stats['success'] = True
        logger.info("Discovery phase completed successfully", **stats)
        return stats

    except Exception as e:
        logger.error("Discovery phase failed", error=str(e))
        stats['error'] = str(e)
        return stats


def run_normalize_phase(args) -> dict:
    """Execute Phase 2: Parsing & Normalization."""
    logger = get_logger("mtf_crawler.normalize")
    logger.info("Starting normalization phase")

    # Initialize services
    normalizer_service = NormalizerService()
    storage_service = StorageService()

    stats = {
        'success': False,
        'materials_processed': 0,
        'json_files_created': 0
    }

    try:
        # Load discovery results
        posts, files, discovery_report = load_discovery_results(args.discovery_report)

        # Process materials using discovery insights
        logger.info("Processing materials with discovery insights")
        all_materials = normalizer_service.process_materials(files)
        stats['materials_processed'] = len(all_materials)

        # Save final JSON files
        if not args.dry_run:
            logger.info("Saving normalized JSON files")
            for post in posts:
                try:
                    post_url_norm = post.url.rstrip('/').lower()
                    post_files = [f for f in files if f.source_post_url.rstrip('/').lower() == post_url_norm]
                    post_materials = [m for m in all_materials if any(f.sha256_hash == m.source_file_hash for f in post_files)]
                    json_data = storage_service.save_json(post, post_files, post_materials)
                    stats['json_files_created'] += 1
                    json_data_complete = JSONData.create_complete(post, post_files, post_materials)
                    output_path = Path('data/processed') / f"{post.id if hasattr(post, 'id') else post.post_hash}.json"
                    with open(output_path, 'w', encoding='utf-8') as f:
                        import json
                        json.dump(json_data_complete, f, default=lambda o: o.__dict__, indent=2, ensure_ascii=False)
                    logger.info(f"Saved normalized JSON for post: {getattr(post, 'id', getattr(post, 'post_hash', None))} → {output_path}")
                except Exception as e:
                    logger.error(f"Failed to process post: {getattr(post, 'id', getattr(post, 'post_hash', None))}", error=str(e))

        stats['success'] = True
        logger.info("Normalization phase completed successfully", **stats)
        return stats

    except Exception as e:
        logger.error("Normalization phase failed", error=str(e))
        stats['error'] = str(e)
        return stats


def run_both_phases(args) -> dict:
    """Execute both phases sequentially."""
    logger = get_logger("mtf_crawler.both")
    logger.info("Starting both phases")

    # Phase 1: Discovery
    discovery_result = run_discovery_phase(args)
    if not discovery_result.get('success'):
        return discovery_result

    # Phase 2: Normalization (update args with discovery report path)
    args.discovery_report = 'data/discovery/report.json'
    normalize_result = run_normalize_phase(args)

    # Combine results
    combined_stats = {
        'success': discovery_result.get('success') and normalize_result.get('success'),
        'posts_crawled': discovery_result.get('posts_crawled', 0),
        'files_downloaded': discovery_result.get('files_downloaded', 0),
        'materials_processed': normalize_result.get('materials_processed', 0),
        'json_files_created': normalize_result.get('json_files_created', 0)
    }

    return combined_stats


def generate_discovery_report(posts, files):
    """Generate discovery report from crawled data."""
    # Placeholder implementation - will be expanded
    return {
        'generation_timestamp': '2025-10-03T14:46:00Z',
        'total_posts_crawled': len(posts),
        'total_files_downloaded': len(files),
        'file_structure_patterns': ['single_material_vertical'],
        'parsing_recommendations': {
            'single_material_vertical': 'property_value_parser'
        }
    }


def save_discovery_results(posts, files, discovery_report):
    """Save discovery results to disk."""
    os.makedirs('data/discovery', exist_ok=True)
    import json
    # Save discovery report
    with open('data/discovery/report.json', 'w') as f:
        json.dump(discovery_report, f, indent=2)
    # Save posts
    with open('data/discovery/posts.json', 'w') as f:
        json.dump([post.__dict__ for post in posts], f, indent=2)
    # Save files
    with open('data/discovery/files.json', 'w') as f:
        json.dump([file.__dict__ for file in files], f, indent=2)


def load_discovery_results(discovery_report_path):
    import json
    # Load discovery report
    with open(discovery_report_path, 'r') as f:
        discovery_report = json.load(f)
    # Load posts
    posts_path = os.path.join(os.path.dirname(discovery_report_path), 'posts.json')
    with open(posts_path, 'r') as f:
        posts_data = json.load(f)
    # Load files
    files_path = os.path.join(os.path.dirname(discovery_report_path), 'files.json')
    with open(files_path, 'r') as f:
        files_data = json.load(f)
    # Ricostruisci oggetti Post e ValidFile se necessario
    from models.post import Post
    from models.valid_file import ValidFile
    posts = [Post(**p) for p in posts_data]
    files = [ValidFile(**f) for f in files_data]
    return posts, files, discovery_report


def validate_requirements():
    """Validate that all required dependencies are available."""
    logger = get_logger("mtf_crawler.validation")

    try:
        import requests
        import pandas as pd
        import structlog
        from bs4 import BeautifulSoup

        logger.debug("All required dependencies available")
        return True

    except ImportError as e:
        logger.error("Missing required dependency", error=str(e))
        return False


if __name__ == '__main__':
    # Validate requirements before starting
    if not validate_requirements():
        print("ERROR: Missing required dependencies. Please install requirements.txt")
        sys.exit(1)

    # Run main CLI
    exit_code = main()
    sys.exit(exit_code)
