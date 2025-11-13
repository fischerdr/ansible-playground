#!/usr/bin/python
# -*- coding: utf-8 -*-


class FilterModule(object):
    """Custom filters for hierarchical lookups."""

    def filters(self):
        return {
            "hierarchical_lookup": self.hierarchical_lookup,
        }

    def hierarchical_lookup(self, data, user, env, region, default_value=None):
        """
        Perform a hierarchical lookup in a nested dictionary with fallbacks.

        Args:
            data (dict): The nested dictionary to search in
            user (str): The user identifier
            env (str): The environment identifier (dev, test, prod)
            region (str): The region identifier
            default_value (str, optional): Default value if no match is found

        Returns:
            The value found in the hierarchy or the default_value
        """
        # Define the lookup paths in order of preference
        lookup_paths = [
            "users.{}.{}.{}".format(user, env, region),
            "users.{}.{}.default".format(user, env),
            "users.{}.default".format(user),
            "users.default.{}.{}".format(env, region),
            "users.default.{}.default".format(env),
            "users.default.default",
            "default",
        ]

        # Try each path in order
        for path in lookup_paths:
            value = self._get_nested_value(data, path)
            if value is not None:
                return value

        # Return the default value if nothing was found
        return default_value

    def _get_nested_value(self, data, path):
        """
        Get a value from a nested dictionary using a dot-separated path.

        Args:
            data (dict): The nested dictionary
            path (str): Dot-separated path to the value

        Returns:
            The value if found, None otherwise
        """
        keys = path.split(".")
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current
