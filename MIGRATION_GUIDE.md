# Info Files Migration Tool

A general-purpose migration script for updating `info.json` files in the OpenVaultFiles repository.

## Features

- Fetch all info.json files from the repository
- Apply custom transformations to the data
- Preview changes before applying them
- Generate files locally or push directly to GitHub
- Automatically create pull requests

## Usage

### Basic Commands

```bash
# Preview changes only (no files created)
python migrate_info_files.py --transform=<function_name>

# Generate files locally in ./migrated_files/
python migrate_info_files.py --transform=<function_name> --generate

# Push directly to GitHub (creates branch and PR)
export GITHUB_TOKEN=your_token_here
python migrate_info_files.py --transform=<function_name> --push --branch=my-migration
```

### Available Transformations

- `years_to_seasons` - Convert `years-used` field to `seasons-used` array
- `example` - Example transformation (adds a sample field)

## Creating Custom Transformations

Add your transformation function to `migrate_info_files.py`:

```python
def my_custom_transform(data: Dict[str, Any], file_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Your custom transformation.
    
    Args:
        data: The current info.json data
        file_info: Additional info (path, section, subsection, folder)
    
    Returns:
        Modified data dict, or None if no changes needed
    """
    # Example: Update a field
    if "old-field" in data:
        data["new-field"] = data["old-field"]
        del data["old-field"]
        return data
    
    return None  # No changes needed

# Register it
TRANSFORM_REGISTRY["my_transform"] = my_custom_transform
```

## Examples

### Example 1: Convert years-used to seasons-used

```bash
# Preview the changes
python migrate_info_files.py --transform=years_to_seasons

# Generate files locally
python migrate_info_files.py --transform=years_to_seasons --generate

# Push to GitHub
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
python migrate_info_files.py --transform=years_to_seasons --push \
    --branch=migrate-years-to-seasons \
    --pr-title="Migrate years-used to seasons-used" \
    --pr-body="Converts all info.json files to use seasons-used array format"
```

### Example 2: Add a new required field

```python
def add_version_field(data: Dict[str, Any], file_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Add version field if missing."""
    if "version" not in data:
        data["version"] = "1.0"
        return data
    return None

TRANSFORM_REGISTRY["add_version"] = add_version_field
```

```bash
python migrate_info_files.py --transform=add_version --generate
```

### Example 3: Update field based on section

```python
def update_by_section(data: Dict[str, Any], file_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Different updates for different sections."""
    section = file_info["section"]
    
    if section == "code" and "language" not in data:
        data["language"] = "Unknown"
        return data
    
    if section == "cad" and "cad-software" not in data:
        data["cad-software"] = "Onshape"
        return data
    
    return None

TRANSFORM_REGISTRY["section_update"] = update_by_section
```

## GitHub Token Setup

For pushing changes, you need a GitHub Personal Access Token:

1. Go to https://github.com/settings/tokens
2. Generate new token (classic)
3. Select `repo` scope
4. Copy the token

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

## Output Structure

When using `--generate`, files are created in `./migrated_files/` with the same structure as the repository:

```
migrated_files/
└── ftc/
    ├── code/
    │   ├── autonomous/
    │   ├── full-repo/
    │   ├── teleop/
    │   └── vision/
    ├── cad/
    │   ├── robots/
    │   ├── claws/
    │   └── ...
    └── portfolios/
        └── portfolios/
```

## Advanced Options

```bash
# Custom branch name
python migrate_info_files.py --transform=my_transform --push --branch=feature/my-update

# With custom PR details
python migrate_info_files.py --transform=my_transform --push \
    --branch=my-migration \
    --pr-title="My Migration Title" \
    --pr-body="Detailed description of changes"
```

## Migration Workflow

1. **Develop** - Write your transformation function
2. **Preview** - Run with `--transform` only to see what will change
3. **Test locally** - Run with `--generate` to create files locally
4. **Verify** - Check the generated files in `./migrated_files/`
5. **Push** - Run with `--push` to create a branch and PR
6. **Review & Merge** - Review the PR on GitHub and merge

## Troubleshooting

**No files modified**: Your transformation is returning `None` for all files. Check your logic.

**GitHub push fails**: Ensure your `GITHUB_TOKEN` is set and has the `repo` scope.

**Branch already exists**: The script will use the existing branch. Delete it first or use a different name.

## Legacy Scripts

The original migration scripts are still available:
- `migrate_years_to_seasons.py` - Original years-to-seasons migration
- `push_migration.py` - Original push script

These are kept for reference but `migrate_info_files.py` is recommended for all new migrations.
