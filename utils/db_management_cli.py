#!/usr/bin/env python
"""
Command-line interface for Neo4j database management operations.
"""
import argparse
import json
from utils.db_management import clear_database, get_database_stats

def main():
    """
    Main CLI entry point for database management utilities.
    """
    parser = argparse.ArgumentParser(description='Neo4j Database Management Utilities')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Clear database command
    clear_parser = subparsers.add_parser('clear', help='Clear all data from the Neo4j database')
    clear_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    
    # Get stats command
    stats_parser = subparsers.add_parser('stats', help='Get statistics about the Neo4j database')
    stats_parser.add_argument('--format', choices=['text', 'json'], default='text', 
                              help='Output format for statistics')
    
    args = parser.parse_args()
    
    if args.command == 'clear':
        if not args.force:
            confirm = input("Are you sure you want to clear all data from the database? This cannot be undone. (y/n): ")
            if confirm.lower() != 'y':
                print("Operation cancelled.")
                return
        
        success = clear_database()
        if success:
            print("Database cleared successfully.")
        else:
            print("Failed to clear database. Check logs for details.")
    
    elif args.command == 'stats':
        stats = get_database_stats()
        if stats:
            if args.format == 'json':
                print(json.dumps(stats, indent=2))
            else:
                print("\nNeo4j Database Statistics:")
                print("-------------------------")
                print(f"Total nodes: {stats.get('total_nodes', 0)}")
                print(f"Total relationships: {stats.get('total_relationships', 0)}")
                
                print("\nNode counts by label:")
                for label, count in stats.get('nodes', {}).items():
                    print(f"  {label}: {count}")
                
                print("\nRelationship counts by type:")
                for rel_type, count in stats.get('relationships', {}).items():
                    print(f"  {rel_type}: {count}")
        else:
            print("Failed to retrieve database statistics.")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
