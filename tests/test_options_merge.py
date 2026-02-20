#!/usr/bin/env python3
"""
Test the option merging logic directly
"""
import sys
sys.path.insert(0, '/home/claude')

from phart import LayoutOptions, NodeStyle
from dataclasses import asdict, fields

# Simulate CLI options (what would come from --ascii --binary-tree flags)
cli_options = LayoutOptions(
    use_ascii=True,
    node_style=NodeStyle.SQUARE,
    binary_tree_layout=False  # CLI didn't enable it
)

# Simulate user code options (what user specifies in their Python file)
user_options = LayoutOptions(
    binary_tree_layout=True,  # User wants this
    layer_spacing=5  # User wants custom spacing
)

print("CLI Options:")
print(f"  use_ascii: {cli_options.use_ascii}")
print(f"  binary_tree_layout: {cli_options.binary_tree_layout}")
print(f"  layer_spacing: {cli_options.layer_spacing}")

print("\nUser Options:")
print(f"  use_ascii: {user_options.use_ascii}")
print(f"  binary_tree_layout: {user_options.binary_tree_layout}")
print(f"  layer_spacing: {user_options.layer_spacing}")

# Test the merge logic from get_options
cli_dict = asdict(cli_options)
user_dict = asdict(user_options)
merged_dict = {}

for field in fields(LayoutOptions):
    field_name = field.name
    if field_name == 'instance_id':
        continue
    
    # CLI takes precedence for rendering options
    if field_name in ['use_ascii', 'node_style', 'node_spacing']:
        cli_val = cli_dict.get(field_name)
        user_val = user_dict.get(field_name)
        merged_dict[field_name] = cli_val if cli_val is not None else user_val
    else:
        # User code controls semantic options
        user_val = user_dict.get(field_name)
        cli_val = cli_dict.get(field_name)
        merged_dict[field_name] = user_val if user_val is not None else cli_val

merged = LayoutOptions(**merged_dict)

print("\nMerged Options (should have CLI's use_ascii + user's binary_tree_layout):")
print(f"  use_ascii: {merged.use_ascii} (expected: True from CLI)")
print(f"  binary_tree_layout: {merged.binary_tree_layout} (expected: True from user)")
print(f"  layer_spacing: {merged.layer_spacing} (expected: 5 from user)")

# Verify expectations
assert merged.use_ascii == True, "use_ascii should come from CLI"
assert merged.binary_tree_layout == True, "binary_tree_layout should come from user"
assert merged.layer_spacing == 5, "layer_spacing should come from user"

print("\n✅ All assertions passed! Merge logic works correctly.")
