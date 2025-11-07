#!/usr/bin/env python3
"""
Dynamic CSV to Hierarchical JSON Converter

Parses a CSV file with dynamic taxonomy columns and creates a hierarchical JSON structure.
All configuration is set in config.ini.

Usage:
    python csv-to-hierarchy.py
    python csv-to-hierarchy.py -c custom-config.ini

Configuration file (config.ini):
    [paths]
    input = data/input.csv
    output = taxon.json

    [ranks]
    family = family,family_zh
    genus = genus,genus_zh
    species = species,species_zh

    [options]
    verbose = true
"""

import sys
import json
import csv
import argparse
import configparser
from pathlib import Path
from datetime import datetime
from collections import OrderedDict
import uuid

# Common taxonomy ranks in order (from highest to lowest)
COMMON_RANKS = [
    'kingdom',
    'phylum',
    'subphylum',
    'superclass',
    'class',
    'subclass',
    'infraclass',
    'superorder',
    'order',
    'suborder',
    'infraorder',
    'superfamily',
    'family',
    'subfamily',
    'tribe',
    'subtribe',
    'genus',
    'subgenus',
    'species',
    'subspecies',
    'variety',
    'form'
]


def load_ranks_from_file(ranks_file):
    """Load rank configuration from JSON file."""
    try:
        with open(ranks_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in ranks file: {e}")
    except Exception as e:
        raise ValueError(f"Error loading ranks file: {e}")


def parse_csv(file_path):
    """Parse CSV file and return list of dictionaries."""
    data = []

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        if not headers:
            raise ValueError("CSV file has no headers")

        for row in reader:
            data.append(row)

    return data, headers


def build_hierarchy_recursive(data, ranks):
    """
    Build hierarchical structure dynamically based on detected ranks.
    """
    def get_or_create_node(parent, rank_value, rank_value_zh, rank_name, is_last_rank):
        """Get or create a node in the hierarchy."""
        if rank_value not in parent:
            if is_last_rank:
                # Last rank holds the actual data records
                parent[rank_value] = {
                    'name': rank_value,
                    'name_zh': rank_value_zh,
                    'key': str(uuid.uuid4()),
                    'rank': rank_name,
                    'records': []
                }
            else:
                # Intermediate rank holds children
                parent[rank_value] = {
                    'name': rank_value,
                    'name_zh': rank_value_zh,
                    'key': str(uuid.uuid4()),
                    'rank': rank_name,
                    'children': {}
                }
        return parent[rank_value]

    # Build hierarchy
    hierarchy = {}

    for i, row in enumerate(data):
        current_level = hierarchy

        # Navigate/create through each rank level
        for rank_idx, rank in enumerate(ranks):
            rank_value = row.get(rank['field'], '').strip()
            rank_value_zh = ''
            if rank_value:
                rank_value_zh = row.get(rank['field_zh'], '').strip()
                if rank_value_zh and rank_value_zh in ['#N/A', 'N/A']:
                    rank_value_zh = ''

            # Handle empty values
            if not rank_value:
                rank_value = f"Unknown__{rank['field']}__"

            is_last_rank = (rank_idx == len(ranks) - 1)

            # Get or create node at this level
            node = get_or_create_node(current_level, rank_value, rank_value_zh, rank['name'], is_last_rank)

            if is_last_rank:
                # Add the complete record to the last rank
                node['records'].append(row)
            else:
                # Move to next level
                current_level = node['children']

    return hierarchy


def build_hierarchy_array(hierarchy_obj, current_rank_idx=0):
    """
    Build hierarchical structure as arrays (easier to iterate).
    """

    def process_level(items_dict):
        """Recursively convert dict structure to array structure."""
        result = []

        for key, node in items_dict.items():
            item = {
                'name': node['name'],
                'rank': node['rank']
            }

            if 'records' in node:
                # Last level - include the records
                item['records'] = node['records']
                item['count'] = len(node['records'])
            elif 'children' in node:
                # Intermediate level - recurse
                item['children'] = process_level(node['children'])
                item['count'] = sum(child['count'] for child in item['children'])

            result.append(item)

        return result

    return process_level(hierarchy_obj)


def generate_stats(hierarchy, ranks):
    """Generate statistics about the hierarchy."""

    def count_nodes(node_dict, level=0):
        """Recursively count nodes at each level."""
        counts = {}

        for key, node in node_dict.items():
            rank = node['rank']
            counts[rank] = counts.get(rank, 0) + 1

            if 'children' in node:
                child_counts = count_nodes(node['children'], level + 1)
                for child_rank, count in child_counts.items():
                    counts[child_rank] = counts.get(child_rank, 0) + count
            elif 'records' in node:
                counts['records'] = counts.get('records', 0) + len(node['records'])

        return counts

    counts = count_nodes(hierarchy)

    # Format stats in rank order
    stats = OrderedDict()
    for rank in ranks:
        if rank['field'] in counts:
            stats[rank['field']] = counts[rank['field']]

    stats['total_records'] = counts.get('records', 0)

    return stats


def flatten_hierarchy_to_species_list(hierarchy_array):
    """
    Flatten the hierarchy to extract all records/species.
    Useful for compatibility with existing field guide code.
    """
    species_list = []

    def extract_records(nodes):
        for node in nodes:
            if 'records' in node:
                species_list.extend(node['records'])
            elif 'children' in node:
                extract_records(node['children'])

    extract_records(hierarchy_array)
    return species_list


def flatten_hierarchy_with_paths(hierarchy_obj):
    """
    Flatten the hierarchy to a single-layer array with ancestor UUID paths.
    Each record gets a 'path' field containing ancestor UUIDs separated by '/'.

    Returns:
        List of dicts with 'path' and 'record' fields
    """
    flat_list = []

    def traverse(node_dict, current_path=''):
        """Recursively traverse and build paths."""
        for key, node in node_dict.items():
            # Build the path with this node's UUID
            node_uuid = node.get('key', '')
            new_path = f"{current_path}/{node_uuid}" if current_path else node_uuid

            if 'records' in node:
                # Leaf node - add all records with the complete path
                for record in node['records']:
                    flat_list.append({
                        'path': new_path,
                        'name': node.get('name', ''),
                        'name_zh': node.get('name_zh', ''),
                        'rank': node.get('rank', ''),
                        'record': record
                    })
            elif 'children' in node:
                # Intermediate node - continue traversing
                traverse(node['children'], new_path)

    traverse(hierarchy_obj)
    return flat_list


def load_config(config_file='config.ini'):
    """Load configuration from INI file."""
    if not Path(config_file).exists():
        print(f"❌ Error: Config file not found: {config_file}", file=sys.stderr)
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(config_file)

    ranks_fields = []
    if 'ranks' in config:
        for k, v in config['ranks'].items():
            fields = v.split(',')
            ranks_fields.append({
                'name': k,
                'field': fields[0].strip(),
                'field_zh': fields[1].strip(),
            })

    return {
        'input': config.get('paths', 'input', fallback=None),
        'output': config.get('paths', 'output', fallback='taxon.json'),
        'ranks_fields': ranks_fields,
        'verbose': config.getboolean('options', 'verbose', fallback=False),
    }

def create_arg_parser():
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description='Convert CSV with taxonomy data to hierarchical JSON structure.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default config.ini
  %(prog)s

  # Use custom config file
  %(prog)s -c custom-config.ini

Config File (config.ini):
  [paths]
  input = data/input.csv
  output = taxon.json

  [ranks]
  family = family,family_zh
  genus = genus,genus_zh
  species = species,species_zh

  [options]
  verbose = true
        """
    )

    parser.add_argument(
        '-c', '--config',
        type=str,
        default='config.ini',
        help='Configuration file path (default: config.ini)'
    )

    return parser


def main():
    # Parse command line arguments
    parser = create_arg_parser()
    args = parser.parse_args()

    # Load configuration from file
    config = load_config(args.config)

    # Get settings from config
    input_file = config['input']
    output_file = config['output']
    ranks_fields = config['ranks_fields']
    verbose = config['verbose']

    # Validate that we have an input file
    if not input_file:
        print(f"❌ Error: No input file specified in {args.config}", file=sys.stderr)
        sys.exit(1)

    # Check if input file exists
    if not Path(input_file).exists():
        print(f"❌ Error: File not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    if verbose:
        print(f"📋 Using configuration:")
        print(f"   Config file: {args.config}")
        print(f"   Input: {input_file}")
        print(f"   Output: {output_file}")
        print(f"   Ranks: {ranks_fields}")

    ranks = ranks_fields

    try:
        print(f"📖 Reading CSV file: {input_file}")
        data, headers = parse_csv(input_file)
        print(f"✓ Parsed {len(data)} rows")

        if verbose:
            print(f"   Columns: {', '.join(headers)}")

        print('\n🔨 Building hierarchy...')
        hierarchy_obj = build_hierarchy_recursive(data, ranks)
        hierarchy_arr = build_hierarchy_array(hierarchy_obj)
        flat_with_paths = flatten_hierarchy_with_paths(hierarchy_obj)
        print(f'✓ Built {len(hierarchy_arr)} top-level nodes')
        print(f'✓ Flattened to {len(flat_with_paths)} records with paths')
        stats = generate_stats(hierarchy_obj, ranks)
        print('\n📊 Statistics:')
        for rank, count in stats.items():
            if rank != 'total_records':
                print(f'   {rank.capitalize()}: {count}')
        print(f'   Total Records: {stats["total_records"]}')

        # Create flattened species list for easy integration
        #species_list = flatten_hierarchy_to_species_list(hierarchy_arr)


        # Build output based on options
        # if args.flat_only:
        #     output = species_list
        # else:
        #     output = {}

        #     if not args.no_metadata:
        #         output['metadata'] = {
        #             'source': Path(input_file).name,
        #             'generatedAt': datetime.now().isoformat(),
        #             'ranks': ranks,
        #             'statistics': dict(stats)
        #         }

        #     if not args.no_object:
        #         output['hierarchyObject'] = hierarchy_obj

        #     if not args.no_array:
        #         output['hierarchyArray'] = hierarchy_arr

        #     output['speciesList'] = species_list
        # Write hierarchy object
        output = hierarchy_obj
        print(f'\n💾 Writing hierarchy to: {output_file}')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        # Write flat list with paths
        output_path = Path(output_file)
        output_flat = f'{output_path.stem}-flat{output_path.suffix}'
        print(f'💾 Writing flat records with paths to: {output_flat}')
        with open(output_flat, 'w', encoding='utf-8') as f:
            json.dump(flat_with_paths, f, indent=2, ensure_ascii=False)

        print('✅ Conversion complete!')

        print('\n📦 Output files:')
        print(f'   ✓ {output_file}: Object-based hierarchy (nested by ranks)')
        print(f'   ✓ {output_flat}: Flat array with ancestor UUID paths')

        if verbose:
            print('\n📝 Flat structure format:')
            print('   Each record has:')
            print('     - path: ancestor UUIDs separated by "/" (e.g., "uuid1/uuid2/uuid3")')
            print('     - name: taxon name at this level')
            print('     - name_zh: Chinese name (if available)')
            print('     - rank: taxonomic rank')
            print('     - record: original CSV row data')

    except Exception as e:
        print(f'\n❌ Error: {e}', file=sys.stderr)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
