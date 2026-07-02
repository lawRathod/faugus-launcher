"""Backup daemon logic (no UI dependencies).

Handles automatic and manual backups of Faugus Launcher configuration,
game data, and metadata.
"""

import calendar
import os
import shutil
from datetime import datetime, timedelta


BACKUP_ITEMS = [
    "banners", "games-backup", "icons", "config.ini",
    "envar.txt", "games.json", "latest-games.txt",
]


def perform_backup(faugus_dir, dest_path):
    """Create a backup zip of Faugus Launcher data.

    Args:
        faugus_dir: Path to the faugus-launcher config directory.
        dest_path: Full path for the output zip file.

    Returns:
        The date string used for the backup filename.
    """
    temp_dir = os.path.join(faugus_dir, "temp-backup")
    os.makedirs(temp_dir, exist_ok=True)

    for item in BACKUP_ITEMS:
        src = os.path.join(faugus_dir, item)
        dst = os.path.join(temp_dir, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        elif os.path.isfile(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)

    marker_path = os.path.join(temp_dir, ".faugus_marker")
    with open(marker_path, "w") as f:
        f.write("faugus-launcher-backup")

    current_date = datetime.now().strftime("%Y-%m-%d")
    zip_path = os.path.join(faugus_dir, f"faugus-launcher-{current_date}")

    shutil.make_archive(zip_path, "zip", temp_dir)
    shutil.rmtree(temp_dir)

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    if os.path.exists(dest_path):
        os.remove(dest_path)

    shutil.move(zip_path + ".zip", dest_path)
    return current_date


def setup_autostart(enable, faugus_dir):
    """Create or remove the autostart desktop file for the backup daemon."""
    autostart_dir = os.path.expanduser("~/.config/autostart")
    desktop_file = os.path.join(autostart_dir, "faugus-backup.desktop")

    if enable:
        os.makedirs(autostart_dir, exist_ok=True)
        with open(desktop_file, "w") as f:
            f.write("[Desktop Entry]\n")
            f.write("Type=Application\n")
            f.write("Name=Faugus Backup Service\n")
            f.write(f"Exec=python -m faugus.backup --daemon {faugus_dir}\n")
            f.write("Hidden=false\n")
            f.write("NoDisplay=false\n")
            f.write("X-GNOME-Autostart-enabled=true\n")
    else:
        if os.path.exists(desktop_file):
            os.remove(desktop_file)


def get_last_monthly_target(today, target_day):
    """Calculate the most recent monthly backup target date."""
    def safe_replace(date_obj, day):
        try:
            return date_obj.replace(day=day)
        except ValueError:
            last_day = calendar.monthrange(date_obj.year, date_obj.month)[1]
            return date_obj.replace(day=last_day)

    current_month_target = safe_replace(today, target_day)
    if today >= current_month_target:
        return current_month_target

    first_day_current_month = today.replace(day=1)
    last_day_prev_month = first_day_current_month - timedelta(days=1)
    return safe_replace(last_day_prev_month, target_day)


def should_run_backup(config):
    """Determine if a backup should run based on the schedule.

    Args:
        config: dict-like with backup-* keys.

    Returns:
        True if a backup should be performed.
    """
    if config.get('backup-auto-enabled', 'False') != 'True':
        return False

    last_backup_str = config.get('backup-last-date', '2000-01-01')
    if not last_backup_str or last_backup_str.strip() == "":
        last_backup_str = '2000-01-01'

    try:
        last_backup = datetime.strptime(last_backup_str, "%Y-%m-%d").date()
    except ValueError:
        last_backup = datetime(2000, 1, 1).date()

    today = datetime.today().date()
    if today <= last_backup:
        return False

    freq = config.get('backup-frequency', 'daily')
    target_day = int(config.get('backup-target-day', '0'))

    if freq == 'daily':
        return True
    elif freq == 'weekly':
        today_dow = today.weekday()
        days_ago = (today_dow - target_day) % 7
        last_target_date = today - timedelta(days=days_ago)
        return last_backup < last_target_date
    elif freq == 'monthly':
        last_target_date = get_last_monthly_target(today, target_day)
        return last_backup < last_target_date

    return False


def load_config(faugus_dir):
    """Load config.ini from the faugus directory (standalone daemon)."""
    config = {}
    config_path = os.path.join(faugus_dir, "config.ini")
    if os.path.isfile(config_path):
        with open(config_path, 'r') as f:
            for line in f.read().splitlines():
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"')
    return config


def save_config(faugus_dir, config):
    """Save config.ini to the faugus directory (standalone daemon)."""
    config_path = os.path.join(faugus_dir, "config.ini")
    with open(config_path, 'w') as f:
        for key, value in config.items():
            if key in ['default-prefix', 'default-runner']:
                f.write(f'{key}="{value}"\n')
            else:
                f.write(f'{key}={value}\n')


def daemon_mode(faugus_dir):
    """Run the backup daemon loop (checks every 4 hours)."""
    import time
    while True:
        try:
            config = load_config(faugus_dir)
            if should_run_backup(config):
                dest_dir = config.get('backup-dest-dir', '')
                if not dest_dir:
                    dest_dir = os.path.expanduser("~")

                current_date = datetime.now().strftime("%Y-%m-%d")
                zip_filename = f"faugus-launcher-{current_date}.zip"
                dest_path = os.path.join(dest_dir, zip_filename)

                new_date = perform_backup(faugus_dir, dest_path)
                config['backup-last-date'] = new_date
                save_config(faugus_dir, config)
        except Exception:
            pass
        time.sleep(14400)
