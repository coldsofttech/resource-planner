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


PERMISSION_CATEGORIES = [
    _PERMISSIONS_CATEGORIES,
]
