# CTF Instance Integration Guide

## Overview

This system allows admins to create challenges that reference existing Docker instances stored in the `CTF_Instances` folder structure. Instead of manually specifying Docker image names, admins can now select from pre-configured instances.

## Architecture

```
CTF_Instances/
├── Web_Instances/
│   └── xss-ashal/
│       ├── app.py
│       ├── requirements.txt
│       ├── Dockerfile
│       ├── instance/
│       ├── static/
│       └── templates/
├── Pwn_Instances/
├── Rev_Instances/
├── Forensics_Instances/
├── Crypto_Instances/
└── OSINT_Instances/
```

## Components Created

### 1. **Instance Manager** (`app/instance_manager.py`)

Utility functions to scan and list available instances:

- `get_available_instances(challenge_type)` - List all instances for a type
- `get_instance_path(challenge_type, instance_name)` - Get full path to instance
- `instance_exists()` - Check if instance exists
- `get_instance_dockerfile_path()` - Get Dockerfile path
- `list_all_instances()` - Get all instances grouped by type

### 2. **Database Model** (`app/models.py`)

Updated `Challenge` model with:

```python
instance_name = db.Column(db.String(255), nullable=True)
```

Stores the folder name of the instance (e.g., "xss-ashal")

### 3. **Admin Form** (`app/admin_forms.py`)

Enhanced `ChallengeForm` with:

- `instance_name` SelectField
- Dynamic population based on challenge type
- `update_instance_choices()` method

### 4. **Admin Routes** (`app/blueprints/admin.py`)

Updated challenge creation/editing:

- Populates instance dropdown based on `type` field
- Saves selected instance to database
- Includes instance info in admin alerts
- New API endpoint: `/admin/api/instances/<challenge_type>`

### 5. **JavaScript** (`app/static/js/instance-selector.js`)

Dynamic dropdown updating:

- Listens for challenge type changes
- Fetches available instances via API
- Updates dropdown in real-time

### 6. **Template** (`app/templates/admin/challenge_form.html`)

Updated form with:

- Instance selection dropdown
- JavaScript integration
- Helper text

## Setup Instructions

### Step 1: Create Instance Folders

✅ Done. Already created:

- `CTF_Instances/Pwn_Instances/`
- `CTF_Instances/Rev_Instances/`
- `CTF_Instances/Web_Instances/` (with xss-ashal)

### Step 2: Add Your Instances

Create instance folders following this structure:

```
CTF_Instances/Web_Instances/my-xss-challenge/
├── app.py                 # Main application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker image definition
├── instance/             # Database/persistent storage
├── static/               # CSS, JS, images
└── templates/            # HTML templates
```

### Step 3: Create Database Migration

```bash
flask db migrate -m "Add instance_name to Challenge model"
flask db upgrade
```

### Step 4: Use in Admin Panel

1. Go to Admin → Add Challenge
2. Fill in basic details
3. Select Challenge Type (Web, Pwn, Rev, etc.)
4. Instance dropdown auto-populates with available instances
5. Select desired instance
6. Save challenge

## Example Workflow

### Creating a Web Challenge with Instance

1. **Admin Panel** → **Challenges** → **Add Challenge**
2. Fill form:
   - Title: "XSS Exploitation"
   - Category: "Web"
   - Type: **"Web"** ← Triggers auto-population
   - Instance: **"xss-ashal"** ← Now appears in dropdown
   - Points: 100
   - Flag: "FLAG{xss_found}"
3. Click "Save Challenge"

Result:

```
Challenge(
    title="XSS Exploitation",
    type="web",
    instance_name="xss-ashal",  # ← New!
    ...
)
```

### Using Instance in Challenge Routes

In your challenge routes, you can now access the instance:

```python
@challenges_bp.route('/challenge/<int:challenge_id>')
def view_challenge(challenge_id):
    chal = Challenge.query.get_or_404(challenge_id)

    if chal.instance_name:
        from app.instance_manager import get_instance_path
        instance_path = get_instance_path(chal.type, chal.instance_name)
        # Use instance_path to serve files, configs, etc.
        print(f"Instance location: {instance_path}")

    return render_template('challenge_detail.html', chal=chal)
```

## File Reference

| File                                      | Purpose                                |
| ----------------------------------------- | -------------------------------------- |
| `app/instance_manager.py`                 | Scan and list CTF instances            |
| `app/models.py`                           | Add `instance_name` field to Challenge |
| `app/admin_forms.py`                      | Dynamic instance selection form        |
| `app/blueprints/admin.py`                 | Handle instance selection in routes    |
| `app/static/js/instance-selector.js`      | Real-time dropdown updates             |
| `app/templates/admin/challenge_form.html` | Updated form UI                        |
| `CTF_Instances/Web_Instances/`            | Web challenge instances                |
| `CTF_Instances/Pwn_Instances/`            | Binary exploitation instances          |
| `CTF_Instances/Rev_Instances/`            | Reverse engineering instances          |

## Supported Challenge Types

```python
INSTANCE_TYPES = {
    'web': 'Web_Instances',
    'pwn': 'Pwn_Instances',
    'forensics': 'Forensics_Instances',
    'rev': 'Rev_Instances',
    'crypto': 'Crypto_Instances',
    'osint': 'OSINT_Instances',
}
```

Add more by:

1. Creating folder: `CTF_Instances/{Type}_Instances/`
2. Adding to `instance_manager.py` `INSTANCE_TYPES` dict
3. Updating form choices in `admin_forms.py`

## API Endpoints

### Get Available Instances

```
GET /admin/api/instances/<challenge_type>

Example:
GET /admin/api/instances/web
Response: ["xss-ashal", "sqli-basic"]
```

## Advanced: Launching Docker Instances

When users solve a challenge with an associated instance, you can:

1. Build Docker image from Dockerfile:

```bash
docker build -t cylvern/xss-ashal CTF_Instances/Web_Instances/xss-ashal/
```

2. Use with Docker launcher (see DOCKER_INSTANCE_SETUP.md):

```python
instance = docker_manager.spawn_instance(
    user_id=current_user.id,
    challenge_id=challenge_id,
    image_name=f"cylvern/{chal.instance_name}"
)
```

## Troubleshooting

### Instances not showing in dropdown

- Check folder exists: `CTF_Instances/{Type}_Instances/`
- Verify folder name matches exactly (case-sensitive)
- Check challenge type is selected before viewing dropdown
- Clear browser cache

### API returns empty list

```bash
# Check instance folders exist
ls CTF_Instances/Web_Instances/

# Verify permissions
ls -la CTF_Instances/Web_Instances/xss-ashal/
```

### Database migration fails

```bash
# Reset migrations if needed
flask db downgrade
flask db upgrade
```

## Next Steps

1. ✅ Create instance folders (Web, Pwn, Rev)
2. ✅ Add instances to folders with Dockerfile
3. ⏳ Run database migration
4. ⏳ Test challenge creation with instance selection
5. ⏳ Build Docker images from instances
6. ⏳ Integrate with Docker launcher system
