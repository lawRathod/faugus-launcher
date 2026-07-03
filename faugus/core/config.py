"""Configuration management with typed accessors.

Wraps the raw config.ini key/value store with type-safe properties
so callers never need to do string comparisons for boolean flags.
"""

import logging
import os

logger = logging.getLogger(__name__)


class AppConfig:
    """Typed wrapper around the INI-style config file.

    Usage::

        cfg = AppConfig(config_file_dir)
        if cfg.close_on_launch:
            ...
        cfg.set("banner-size", 120)
        cfg.save()
    """

    _BOOLEANS = {
        'close-onlaunch': False,
        'mangohud': False,
        'gamemode': False,
        'disable-hidraw': False,
        'prevent-sleep': False,
        'discrete-gpu': False,
        'splash-disable': False,
        'system-tray': False,
        'start-boot': False,
        'mono-icon': False,
        'show-labels': False,
        'enable-logging': False,
        'wayland-driver': False,
        'enable-wow64': False,
        'logging-warning': False,
        'show-hidden': False,
        'disable-updates': False,
        'show-donate': True,
        'gamepad-navigation': False,
        'start-minimized': False,
        'show-categories': False,
        'backup-auto-enabled': False,
        'show-sidebar': True,
    }

    _DEFAULTS = {
        'default-prefix': '',
        'default-runner': 'Proton-CachyOS Latest',
        'lossless-location': '',
        'language': '',
        'donate-last': '',
        'interface-mode': 'List',
        'backup-frequency': 'daily',
        'backup-target-day': '0',
        'backup-dest-dir': '',
        'backup-last-date': '',
        'window-behavior': 'None',
        'width': '1280',
        'height': '720',
        'banner-size': '100',
        'sort': 'alpha',
        'category': 'all',
        'current-view': 'library',
        'playtime': '0',
    }

    def __init__(self, config_file):
        self._config_file = config_file
        self._config = {}
        self._load()

    # -- Low-level I/O -------------------------------------------------------

    def _load(self):
        """Read config.ini into memory, filling missing keys with defaults."""
        logger.debug("Loading config from %s", self._config_file)
        if os.path.isfile(self._config_file):
            with open(self._config_file, 'r') as f:
                for line in f.read().splitlines():
                    if '=' in line:
                        key, value = line.split('=', 1)
                        self._config[key.strip()] = value.strip().strip('"')
            logger.debug("Loaded %d keys from file", len(self._config))

        updated = False
        all_defaults = {**self._BOOLEANS, **self._DEFAULTS}
        for key, default_value in all_defaults.items():
            if key not in self._config:
                str_val = str(default_value) if not isinstance(default_value, bool) else str(default_value)
                self._config[key] = str_val
                updated = True
                logger.debug("Filled default for missing key %s=%s", key, str_val)

        if updated or not os.path.isfile(self._config_file):
            logger.debug("Config updated or file missing, saving")
            self.save()
        else:
            logger.debug("Config loaded, no changes needed")

    def save(self):
        """Write the current config to disk."""
        config_dir = os.path.dirname(self._config_file)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir)

        with open(self._config_file, 'w') as f:
            for key, value in self._config.items():
                if key in ('default-prefix', 'default-runner'):
                    f.write(f'{key}="{value}"\n')
                else:
                    f.write(f'{key}={value}\n')
        logger.debug("Saved config to %s (%d keys)", self._config_file, len(self._config))

    def get(self, key, default=''):
        """Get a raw config value as a string."""
        return self._config.get(key, default)

    def set(self, key, value):
        """Set a config value. Silently ignores unknown keys."""
        all_keys = set(self._BOOLEANS.keys()) | set(self._DEFAULTS.keys())
        if key not in all_keys:
            return
        self._config[key] = str(value)

    # -- Typed boolean accessors --------------------------------------------

    def _bool(self, key):
        return self._config.get(key, 'False') == 'True'

    @property
    def close_on_launch(self):
        return self._bool('close-onlaunch')

    @property
    def mangohud(self):
        return self._bool('mangohud')

    @property
    def gamemode(self):
        return self._bool('gamemode')

    @property
    def disable_hidraw(self):
        return self._bool('disable-hidraw')

    @property
    def prevent_sleep(self):
        return self._bool('prevent-sleep')

    @property
    def discrete_gpu(self):
        return self._bool('discrete-gpu')

    @property
    def splash_disable(self):
        return self._bool('splash-disable')

    @property
    def system_tray(self):
        return self._bool('system-tray')

    @property
    def start_boot(self):
        return self._bool('start-boot')

    @property
    def mono_icon(self):
        return self._bool('mono-icon')

    @property
    def show_labels(self):
        return self._bool('show-labels')

    @property
    def enable_logging(self):
        return self._bool('enable-logging')

    @property
    def wayland_driver(self):
        return self._bool('wayland-driver')

    @property
    def enable_wow64(self):
        return self._bool('enable-wow64')

    @property
    def logging_warning(self):
        return self._bool('logging-warning')

    @property
    def show_hidden(self):
        return self._bool('show-hidden')

    @property
    def disable_updates(self):
        return self._bool('disable-updates')

    @property
    def show_donate(self):
        return self._bool('show-donate')

    @property
    def gamepad_navigation(self):
        return self._bool('gamepad-navigation')

    @property
    def start_minimized(self):
        return self._bool('start-minimized')

    @property
    def show_categories(self):
        return self._bool('show-categories')

    @property
    def backup_auto_enabled(self):
        return self._bool('backup-auto-enabled')

    @property
    def show_sidebar(self):
        return self._bool('show-sidebar')

    # -- Typed value accessors -----------------------------------------------

    @property
    def default_prefix(self):
        return self._config.get('default-prefix', '')

    @property
    def default_runner(self):
        return self._config.get('default-runner', 'Proton-CachyOS Latest')

    @property
    def lossless_location(self):
        return self._config.get('lossless-location', '')

    @property
    def language(self):
        return self._config.get('language', '')

    @property
    def donate_last(self):
        return self._config.get('donate-last', '')

    @property
    def interface_mode(self):
        return self._config.get('interface-mode', 'List')

    @property
    def backup_frequency(self):
        return self._config.get('backup-frequency', 'daily')

    @property
    def backup_target_day(self):
        return int(self._config.get('backup-target-day', '0'))

    @property
    def backup_dest_dir(self):
        return self._config.get('backup-dest-dir', '')

    @property
    def backup_last_date(self):
        return self._config.get('backup-last-date', '')

    @property
    def window_behavior(self):
        return self._config.get('window-behavior', 'None')

    @property
    def width(self):
        return int(self._config.get('width', '1280'))

    @property
    def height(self):
        return int(self._config.get('height', '720'))

    @property
    def banner_size(self):
        return int(self._config.get('banner-size', '100'))

    @property
    def sort(self):
        return self._config.get('sort', 'alpha')

    @property
    def category(self):
        return self._config.get('category', 'all')

    @property
    def current_view(self):
        return self._config.get('current-view', 'library')

    @property
    def playtime(self):
        return int(self._config.get('playtime', '0'))

    @playtime.setter
    def playtime(self, value):
        self._config['playtime'] = str(int(value))
