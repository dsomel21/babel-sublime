import sublime
import sublime_plugin


__all__ = ['BuildBabelPackageCommand']


BABEL_CONFIGURATION = {
    'name': 'JavaScript (Babel)',
    'scope': 'source.js',
    'file_extensions': [ 'js', 'jsx', 'es6', 'babel' ],
    'flow_types': True,
    'jsx': True,
    'string_object_keys': True,
    'custom_templates': {
        'styled_components': True,
    },
}


class BuildBabelPackageCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        from sublime_lib import ResourcePath
        from pathlib import Path
        from shutil import rmtree

        try:
            package_path = Path(__file__).parent.parent
            syntax_path = ResourcePath.from_file_path(package_path) / 'JavaScript (Babel).sublime-syntax'
            test_directory = package_path / 'tests'

            # Validate package path exists
            if not package_path.exists():
                sublime.error_message("Package path does not exist: {}".format(package_path))
                return

            # Clean and recreate test directory
            try:
                rmtree(str(test_directory), ignore_errors=True)
                test_directory.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                sublime.error_message("Failed to create test directory: {}".format(e))
                return

            # Validate that JS Custom is available
            try:
                js_custom_path = ResourcePath('Packages/JSCustom/styled_components/Styled Components.sublime-syntax')
                if not js_custom_path.exists():
                    sublime.error_message(
                        "JS Custom package not found. Please install JS Custom from Package Control."
                    )
                    return
            except Exception as e:
                sublime.error_message("Failed to validate JS Custom dependency: {}".format(e))
                return

            # Get active window with validation
            window = sublime.active_window()
            if window is None:
                sublime.error_message("No active window available. Please open a file first.")
                return

            print("Building syntax…")
            window.run_command('build_js_custom_syntax', {
                'name': 'Babel',
                'configuration': BABEL_CONFIGURATION,
                'destination_path': str(syntax_path.file_path()),
            })

            # Validate syntax file was created
            if not syntax_path.exists():
                sublime.error_message("Failed to generate syntax file. Check console for errors.")
                return

            # Copy styled components syntax
            try:
                js_custom_path.copy(
                    (ResourcePath.from_file_path(package_path) / 'Styled Components.sublime-syntax').file_path()
                )
            except Exception as e:
                sublime.error_message("Failed to copy Styled Components syntax: {}".format(e))
                return

            print("Building tests…")
            sublime.run_command('build_js_custom_tests', {
                'syntax_path': str(syntax_path),
                'suites': ['js', 'flow', 'jsx', 'string_object_keys'],
                'destination_directory': str(test_directory),
            })

            # Validate tests were created
            test_files = list(test_directory.glob('*.js')) + list(test_directory.glob('*.jsx'))
            if not test_files:
                sublime.error_message("No test files were generated. Check console for errors.")
                return

            print('Done. Generated {} test files.'.format(len(test_files)))

        except Exception as e:
            error_msg = "Build failed with error: {}".format(e)
            print(error_msg)
            sublime.error_message(error_msg)
            raise
