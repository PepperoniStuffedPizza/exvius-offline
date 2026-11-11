"""Android binding for the existing local game engine and bundled data."""
import json
import os
from pathlib import Path


def start(writable_root, data_root=None):
    if data_root is None:
        import exvius_pack
        static = Path(exvius_pack.__file__).parent
    else:
        static = Path(data_root)
    for key, relative in (
        ('MST_DIR', 'mst_decoded'), ('TEXT_DIR', 'text_decoded'),
        ('ART_ROOT', 'cpk_extract'), ('CDN_ROOT', 'client/files'),
        ('COMMUNITY_ART_ROOT', 'gacha_community/art'),
        ('CDN_OVERLAY', 'overlay'), ('VERSION_TABLE_XML', 'client/shared_prefs/gamedata.xml'),
    ):
        os.environ[key] = str(static / relative)
    root = Path(writable_root)
    root.mkdir(parents=True, exist_ok=True)
    native_files = root.parent
    if (native_files / 'mst').is_dir() and (native_files / 'common_lang').is_dir():
        # Content availability is consulted while LocalGame loads the save.
        # Bind the real native cache before that initialization takes place.
        os.environ['CDN_ROOT'] = str(native_files)
        os.environ['CDN_OVERLAY'] = str(native_files)
    from local_game import LocalGame
    game = LocalGame(root)
    if (native_files / 'mst').is_dir() and (native_files / 'common_lang').is_dir():
        game.server.State.cdn_root = str(native_files)
        # Index the native cache where the original Android game stores images.
        from ffbe_gacha import BANNER_ART_ROOTS, _BANNER_ART_INDEX
        for relative in ('homeMarquee', 'en/sd/static_banner', 'common_lang/sd/static_banner'):
            native_art = str(native_files / relative)
            if native_art not in BANNER_ART_ROOTS:
                BANNER_ART_ROOTS.append(native_art)
                _BANNER_ART_INDEX.clear()
    return game


def request(game, method, path, body, headers):
    try:
        return game.request(str(method), str(path), bytes(body), json.loads(str(headers)))
    except Exception as error:
        # Report only code locations, never request bodies, headers or saves.
        import traceback
        frames = traceback.extract_tb(error.__traceback__)
        print('LOCAL_REQUEST_FAILED type=' + type(error).__name__ + ' at=' +
              '>'.join(frame.name + ':' + str(frame.lineno) for frame in frames), flush=True)
        raise


def summon_archive(game, selection=''):
    from ffbe_gacha import all_banners, missing_gacha_names
    from gacha_archive import menu
    with game.server.STATE_LOCK:
        player = game.server.State.player
        banners = all_banners()
        result = menu(player, banners, str(selection))
        result['names'] = missing_gacha_names(banners)
        result['limited_steps'] = [int(b['id']) for b in banners if b.get('steps') and b.get('tab') == 'limited']
        result['explanations'] = {str(b['id']): (
            'Choose a unit or prism from the selection list.' if b.get('selection') else
            str(len(b['steps'])) + '-step summon. Review each step\'s contents above.' if b.get('steps') else
            'Summon ' + str(b.get('draws', 1)) + ' reward(s). The button shows the cost. See Drop Rates for the reward list.')
            for b in banners}
        if selection:
            player.save(game.server.st.STATE_FILE, force=True)
        return json.dumps(result)


def event_archive(game, selection=''):
    from event_archive import menu
    with game.server.STATE_LOCK:
        player = game.server.State.player
        result = menu(player, str(selection))
        if selection:
            player.save(game.server.st.STATE_FILE, force=True)
        return json.dumps(result)


def shop_archive(game, selection=''):
    from exvius_shop_catalogue import labels
    return json.dumps(labels())


def raid_action(game, actor, skill, party):
    from exvius_raid_progress import record_party_action
    with game.server.STATE_LOCK:
        player = game.server.State.player
        changed = record_party_action(player, str(actor), int(skill), json.loads(str(party)))
        if changed:
            player.save(game.server.st.STATE_FILE, force=True)
        return changed


LAPIS_GRANT_MAX = 1000000
SAVE_IMPORT_MAX_BYTES = 128 * 1024 * 1024


def grant_lapis(game, amount):
    """Add free Lapis to the existing save and write it. Returns the new balances as JSON."""
    amount = int(amount)
    if not 0 < amount <= LAPIS_GRANT_MAX:
        raise ValueError('Lapis amount must be between 1 and ' + str(LAPIS_GRANT_MAX))
    server = game.server
    with server.STATE_LOCK:
        player = server.State.player
        if player is None or not Path(server.st.STATE_FILE).is_file():
            raise ValueError('Start a game first, then add Lapis.')
        player.add_currency('lapis_free', amount)
        if not player.save(server.st.STATE_FILE):
            raise OSError('The save could not be written. The Lapis was not kept.')
        server.State.state_dirty = False
        return json.dumps({'added': amount,
                           'free': int(player.currencies.get('lapis_free', 0)),
                           'paid': int(player.currencies.get('lapis_paid', 0))})


def export_save(game):
    """The current save as JSON text, taken from the engine under its lock (never a half-written file)."""
    from player_state import _serialise
    server = game.server
    with server.STATE_LOCK:
        player = server.State.player
        if player is None or not Path(server.st.STATE_FILE).is_file():
            raise ValueError('There is no local save to back up yet.')
        # The same view an ordinary autosave writes: no test overlays, no season-only switch bits.
        return json.dumps(_serialise(player._persist_view(force=False)), indent=1)


def import_save(game, text):
    """Validate a backed-up save, keep a copy of the current one, then replace it atomically.

    The caller must restart the app afterwards so the engine reloads the new save through its
    normal start-up path; nothing in the running client is refreshed here.
    """
    import shutil
    import tempfile
    import time
    from player_state import PlayerState
    text = str(text)
    if len(text.encode('utf-8')) > SAVE_IMPORT_MAX_BYTES:
        raise ValueError('That file is too large to be an Exvius save.')
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError('That file is not valid JSON.') from error
    if not isinstance(raw, dict) or 'currencies' not in raw or 'roster' not in raw:
        raise ValueError('That file is not an Exvius Offline save.')
    server = game.server
    with server.STATE_LOCK:
        destination = Path(server.st.STATE_FILE)
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, candidate = tempfile.mkstemp(prefix='import-', suffix='.json', dir=str(destination.parent))
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as handle:
                handle.write(text)
            # The engine's own loader: migrates old files and refuses incoherent ones (raises ValueError).
            imported = PlayerState.load(candidate, slot=server.st.STATE_SLOT, mode='live')
        finally:
            if os.path.exists(candidate):
                os.remove(candidate)
        if destination.exists():
            recovery = destination.parent / 'backups'
            recovery.mkdir(exist_ok=True)
            shutil.copyfile(destination, recovery / (destination.stem + '-before-import-' +
                                                     str(time.time_ns()) + '.json'))
        imported.data.setdefault('meta', {})['offline_started'] = True
        if not imported.save(str(destination), force=True):
            raise OSError('The imported save could not be written. The previous save is unchanged.')
        server.State.player = imported
        server.State.state_dirty = False
        return json.dumps({'name': imported.data['identity']['handle_name'],
                           'rank': imported.data['rank']['level']})


def title_action(game, action):
    from offline_menu import new_game, status
    server = game.server
    with server.STATE_LOCK:
        if action == 'new':
            result = new_game(server.State, server.st.STATE_FILE, server.st.STATE_SLOT)
        elif action == 'status':
            result = status(server.State, server.st.STATE_FILE)
        else:
            raise ValueError('Unknown title action: ' + str(action))
    return json.dumps(result)
