import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.linter import (
    Linter, LintError, load_config, parse_yaml, write_default_config,
    DEFAULT_CONFIG, format_errors
)


class TestLinter(unittest.TestCase):

    def setUp(self):
        self.linter = Linter()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def write_temp_file(self, content: str, name: str = 'test.py') -> str:
        path = os.path.join(self.temp_dir, name)
        with open(path, 'w') as f:
            f.write(content)
        return path

    def test_line_length_ok(self):
        code = 'x = 1\n'
        path = self.write_temp_file(code)
        errors = self.linter.lint_file(path)
        line_errors = [e for e in errors if e.code == 'L001']
        self.assertEqual(len(line_errors), 0)

    def test_line_length_exceeded(self):
        code = 'x = "' + 'a' * 100 + '"\n'
        path = self.write_temp_file(code)
        errors = self.linter.lint_file(path)
        line_errors = [e for e in errors if e.code == 'L001']
        self.assertEqual(len(line_errors), 1)

    def test_trailing_whitespace(self):
        code = 'x = 1   \n'
        path = self.write_temp_file(code)
        errors = self.linter.lint_file(path)
        ws_errors = [e for e in errors if e.code == 'W001']
        self.assertEqual(len(ws_errors), 1)

    def test_no_trailing_whitespace(self):
        code = 'x = 1\n'
        path = self.write_temp_file(code)
        errors = self.linter.lint_file(path)
        ws_errors = [e for e in errors if e.code == 'W001']
        self.assertEqual(len(ws_errors), 0)

    def test_too_many_blank_lines(self):
        code = 'x = 1\n\n\n\n\ny = 2\n'
        path = self.write_temp_file(code)
        errors = self.linter.lint_file(path)
        blank_errors = [e for e in errors if e.code == 'B001']
        self.assertEqual(len(blank_errors), 1)

    def test_acceptable_blank_lines(self):
        code = 'x = 1\n\n\ny = 2\n'
        path = self.write_temp_file(code)
        errors = self.linter.lint_file(path)
        blank_errors = [e for e in errors if e.code == 'B001']
        self.assertEqual(len(blank_errors), 0)

    def test_tab_indentation_error(self):
        code = '\tx = 1\n'
        path = self.write_temp_file(code)
        errors = self.linter.lint_file(path)
        indent_errors = [e for e in errors if e.code == 'I001']
        self.assertEqual(len(indent_errors), 1)

    def test_space_indentation_ok(self):
        code = '    x = 1\n'
        path = self.write_temp_file(code)
        errors = self.linter.lint_file(path)
        indent_errors = [e for e in errors if e.code == 'I001']
        self.assertEqual(len(indent_errors), 0)

    def test_wrong_indent_size(self):
        code = '   x = 1\n'
        path = self.write_temp_file(code)
        errors = self.linter.lint_file(path)
        indent_errors = [e for e in errors if e.code == 'I002']
        self.assertEqual(len(indent_errors), 1)

    def test_no_final_newline(self):
        code = 'x = 1'
        path = self.write_temp_file(code)
        errors = self.linter.lint_file(path)
        newline_errors = [e for e in errors if e.code == 'N001']
        self.assertEqual(len(newline_errors), 1)

    def test_final_newline_present(self):
        code = 'x = 1\n'
        path = self.write_temp_file(code)
        errors = self.linter.lint_file(path)
        newline_errors = [e for e in errors if e.code == 'N001']
        self.assertEqual(len(newline_errors), 0)

    def test_file_not_found(self):
        errors = self.linter.lint_file('/nonexistent/file.py')
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].code, 'E001')

    def test_non_python_file_ignored(self):
        path = self.write_temp_file('hello world', 'test.txt')
        errors = self.linter.lint_file(path)
        self.assertEqual(len(errors), 0)

    def test_custom_config(self):
        linter = Linter({'line_length': 10})
        code = '12345678901234567890\n'
        path = self.write_temp_file(code)
        errors = linter.lint_file(path)
        line_errors = [e for e in errors if e.code == 'L001']
        self.assertEqual(len(line_errors), 1)


class TestParseYaml(unittest.TestCase):

    def test_parse_simple(self):
        content = 'line_length: 100\nindent_size: 2'
        result = parse_yaml(content)
        self.assertEqual(result['line_length'], 100)
        self.assertEqual(result['indent_size'], 2)

    def test_parse_bool(self):
        content = 'trailing_whitespace: true\ntab_indent: false'
        result = parse_yaml(content)
        self.assertTrue(result['trailing_whitespace'])
        self.assertFalse(result['tab_indent'])

    def test_parse_comments(self):
        content = '# comment\nline_length: 80'
        result = parse_yaml(content)
        self.assertEqual(result['line_length'], 80)
        self.assertNotIn('#', result)


class TestLoadConfig(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_yaml(self):
        path = os.path.join(self.temp_dir, 'config.yaml')
        with open(path, 'w') as f:
            f.write('line_length: 120\n')
        result = load_config(path)
        self.assertEqual(result['line_length'], 120)

    def test_load_yml(self):
        path = os.path.join(self.temp_dir, 'config.yml')
        with open(path, 'w') as f:
            f.write('line_length: 100\n')
        result = load_config(path)
        self.assertEqual(result['line_length'], 100)

    def test_wrong_extension(self):
        path = os.path.join(self.temp_dir, 'config.json')
        with open(path, 'w') as f:
            f.write('{}')
        with self.assertRaises(ValueError):
            load_config(path)

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            load_config('/nonexistent.yaml')


class TestWriteDefaultConfig(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_write_config(self):
        path = os.path.join(self.temp_dir, 'plack.yaml')
        write_default_config(path)
        self.assertTrue(os.path.exists(path))
        with open(path) as f:
            content = f.read()
        self.assertIn('line_length: 88', content)


class TestFormatErrors(unittest.TestCase):

    def test_format_no_errors(self):
        result = format_errors([])
        self.assertEqual(result, '')

    def test_format_single_error(self):
        errors = [LintError('test.py', 1, 1, 'E001', 'Test error')]
        result = format_errors(errors, color=False)
        self.assertIn('test.py:1:1:', result)
        self.assertIn('E001', result)

    def test_format_multiple_errors(self):
        errors = [
            LintError('test.py', 1, 1, 'E001', 'Error 1'),
            LintError('test.py', 2, 1, 'W001', 'Warning 1'),
        ]
        result = format_errors(errors, color=False)
        lines = result.split('\n')
        self.assertEqual(len(lines), 2)


class TestLintDirectory(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.linter = Linter()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_lint_directory(self):
        path1 = os.path.join(self.temp_dir, 'test1.py')
        path2 = os.path.join(self.temp_dir, 'test2.py')
        with open(path1, 'w') as f:
            f.write('x = 1\n')
        with open(path2, 'w') as f:
            f.write('y = 2    \n')

        errors = self.linter.lint_directory(self.temp_dir)
        ws_errors = [e for e in errors if e.code == 'W001']
        self.assertEqual(len(ws_errors), 1)

    def test_lint_recursive(self):
        subdir = os.path.join(self.temp_dir, 'sub')
        os.makedirs(subdir)
        path = os.path.join(subdir, 'test.py')
        with open(path, 'w') as f:
            f.write('x = 1    \n')

        errors = self.linter.lint_directory(self.temp_dir, recursive=True)
        ws_errors = [e for e in errors if e.code == 'W001']
        self.assertEqual(len(ws_errors), 1)

    def test_lint_non_recursive(self):
        subdir = os.path.join(self.temp_dir, 'sub')
        os.makedirs(subdir)
        path = os.path.join(subdir, 'test.py')
        with open(path, 'w') as f:
            f.write('x = 1    \n')

        errors = self.linter.lint_directory(self.temp_dir, recursive=False)
        self.assertEqual(len(errors), 0)


if __name__ == '__main__':
    unittest.main()
