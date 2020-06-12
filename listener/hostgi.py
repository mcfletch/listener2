try:
    import gi
except ImportError:
    try:
        import subprocess

        subprocess.check_call(['venv-hpl', 'gi'])
    except subprocess.CalledProcessError:
        raise ImportError("gi")
    else:
        import gi
