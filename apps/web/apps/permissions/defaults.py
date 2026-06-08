_PERMISSIONS_CATEGORIES = {
    "module": "permissions",
    "entries": [
        {
            "name": "View",
            "codename": "view",
            "order": 1,
            "perms": [
                "permissions.view_grouppermissioncategory",
                "permissions.view_userpermissioncategory",
            ],
        },
        {
            "name": "Manage Groups",
            "codename": "manage_groups",
            "order": 2,
            "perms": [
                "permissions.view_grouppermissioncategory",
                "permissions.add_grouppermissioncategory",
                "permissions.change_grouppermissioncategory",
                "permissions.delete_grouppermissioncategory",
            ],
        },
        {
            "name": "Manage Users",
            "codename": "manage_users",
            "order": 3,
            "perms": [
                "permissions.view_userpermissioncategory",
                "permissions.add_userpermissioncategory",
                "permissions.change_userpermissioncategory",
                "permissions.delete_userpermissioncategory",
            ],
        },
        {
            "name": "Manage",
            "codename": "manage",
            "order": 4,
            "perms": [
                "permissions.view_grouppermissioncategory",
                "permissions.add_grouppermissioncategory",
                "permissions.change_grouppermissioncategory",
                "permissions.delete_grouppermissioncategory",
                "permissions.view_userpermissioncategory",
                "permissions.add_userpermissioncategory",
                "permissions.change_userpermissioncategory",
                "permissions.delete_userpermissioncategory",
            ],
        },
    ],
}

_TEAMS_CATEGORIES = {
    "module": "teams",
    "entries": [
        {
            "name": "View",
            "codename": "view",
            "order": 1,
            "perms": [
                "teams.view_team",
            ],
        },
        {
            "name": "Manage",
            "codename": "manage",
            "order": 2,
            "perms": [
                "teams.view_team",
                "teams.add_team",
                "teams.change_team",
                "teams.delete_team",
            ],
        },
        {
            "name": "Import",
            "codename": "import",
            "order": 3,
            "perms": [
                "teams.view_team",
                "teams.import_team",
            ],
        },
        {
            "name": "Export",
            "codename": "export",
            "order": 4,
            "perms": [
                "teams.view_team",
                "teams.export_team",
            ],
        },
    ],
}


_SKILLS_CATEGORIES = {
    "module": "skills",
    "entries": [
        {
            "name": "View",
            "codename": "view",
            "order": 1,
            "perms": [
                "skills.view_skill",
            ],
        },
        {
            "name": "Manage",
            "codename": "manage",
            "order": 2,
            "perms": [
                "skills.view_skill",
                "skills.add_skill",
                "skills.change_skill",
                "skills.delete_skill",
            ],
        },
        {
            "name": "Import",
            "codename": "import",
            "order": 3,
            "perms": [
                "skills.view_skill",
                "skills.import_skill",
            ],
        },
        {
            "name": "Export",
            "codename": "export",
            "order": 4,
            "perms": [
                "skills.view_skill",
                "skills.export_skill",
            ],
        },
    ],
}


_LOCATIONS_CATEGORIES = {
    "module": "locations",
    "entries": [
        {
            "name": "View",
            "codename": "view",
            "order": 1,
            "perms": [
                "locations.view_location",
            ],
        },
        {
            "name": "Manage",
            "codename": "manage",
            "order": 2,
            "perms": [
                "locations.view_location",
                "locations.add_location",
                "locations.change_location",
                "locations.delete_location",
            ],
        },
        {
            "name": "Import",
            "codename": "import",
            "order": 3,
            "perms": [
                "locations.view_location",
                "locations.import_location",
            ],
        },
        {
            "name": "Export",
            "codename": "export",
            "order": 4,
            "perms": [
                "locations.view_location",
                "locations.export_location",
            ],
        },
    ],
}


_EMPLOYMENT_TYPES_CATEGORIES = {
    "module": "employment_types",
    "entries": [
        {
            "name": "View",
            "codename": "view",
            "order": 1,
            "perms": [
                "employment_types.view_employmenttype",
            ],
        },
        {
            "name": "Manage",
            "codename": "manage",
            "order": 2,
            "perms": [
                "employment_types.view_employmenttype",
                "employment_types.add_employmenttype",
                "employment_types.change_employmenttype",
                "employment_types.delete_employmenttype",
            ],
        },
        {
            "name": "Import",
            "codename": "import",
            "order": 3,
            "perms": [
                "employment_types.view_employmenttype",
                "employment_types.import_employmenttype",
            ],
        },
        {
            "name": "Export",
            "codename": "export",
            "order": 4,
            "perms": [
                "employment_types.view_employmenttype",
                "employment_types.export_employmenttype",
            ],
        },
    ],
}


_USERS_CATEGORIES = {
    "module": "users",
    "entries": [
        {
            "name": "View",
            "codename": "view",
            "order": 1,
            "perms": ["auth.view_user", "users.view_useravatar"],
        },
        {
            "name": "Manage",
            "codename": "manage",
            "order": 2,
            "perms": [
                "auth.view_user",
                "auth.add_user",
                "auth.change_user",
                "auth.delete_user",
                "users.view_useravatar",
                "users.add_useravatar",
                "users.change_useravatar",
                "users.delete_useravatar",
            ],
        },
        {
            "name": "Manage Workforce",
            "codename": "manage_workforce",
            "order": 3,
            "perms": [
                "auth.view_user",
                "users.change_user_workforce",
            ],
        },
        {
            "name": "Export",
            "codename": "export",
            "order": 4,
            "perms": [
                "auth.view_user",
                "users.export_member",
            ],
        },
    ],
}


PERMISSION_CATEGORIES = [
    _PERMISSIONS_CATEGORIES,
    _TEAMS_CATEGORIES,
    _SKILLS_CATEGORIES,
    _LOCATIONS_CATEGORIES,
    _EMPLOYMENT_TYPES_CATEGORIES,
    _USERS_CATEGORIES,
]
