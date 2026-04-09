"""
test_main.py - Unit tests for the main module

Tests the main entry point and command-line argument parsing.
"""

import pytest
from io import StringIO
from pathlib import Path
from unittest.mock import patch
from shatranj import main


def workspace_save_file(name: str, content: str) -> Path:
    path = Path(".tmp_main_tests")
    path.mkdir(exist_ok=True)
    save_file = path / name
    save_file.write_text(content, encoding="ascii")
    return save_file


class TestMainEntryPoint:
    """Tests for the main entry point."""

    def test_main_no_args(self):
        """Run main with no arguments."""
        with patch("sys.argv", ["shatranj"]):
            with patch(
                "shatranj.presentation.cli.cli.CLI.run"
            ) as mock_cli_run:
                mock_cli_run.return_value = 0
                result = main.main()
                assert result == 0
                mock_cli_run.assert_called_once()

    def test_main_cli_mode(self):
        """Run main with CLI mode."""
        with patch("sys.argv", ["shatranj", "cli"]):
            with patch(
                "shatranj.presentation.cli.cli.CLI.run"
            ) as mock_cli_run:
                mock_cli_run.return_value = 0
                result = main.main()
                assert result == 0
                mock_cli_run.assert_called_once()

    def test_main_gui_mode(self):
        """Run main with GUI mode."""
        with patch("sys.argv", ["shatranj", "--gui"]):
            with patch(
                "shatranj.presentation.gui.app.run_gui"
            ) as mock_run_gui:
                mock_run_gui.return_value = 0
                result = main.main()
                assert result == 0
                mock_run_gui.assert_called_once()

    def test_main_gui_mode_fails(self):
        """Run main with GUI mode that fails."""
        with patch("sys.argv", ["shatranj", "--gui"]):
            with patch(
                "shatranj.presentation.gui.app.run_gui"
            ) as mock_run_gui:
                mock_run_gui.return_value = 1
                result = main.main()
                assert result == 1

    def test_main_server_mode(self):
        """Run main with dedicated multiplayer server mode."""
        with patch("sys.argv", ["shatranj", "--server", "12345"]):
            with patch(
                "shatranj.domain.network.DiscoveryServer"
            ) as MockDiscovery:
                with patch(
                    "shatranj.domain.network.GameServer"
                ) as MockServer:
                    with patch(
                        "shatranj.main.time.sleep",
                        side_effect=KeyboardInterrupt,
                    ):
                        result = main.main()

        assert result == 0
        MockDiscovery.assert_called_once_with(
            "ShatranjServer",
            12345,
            main.VERSION,
        )
        MockServer.assert_called_once_with("ShatranjServer", 12345)
        MockDiscovery.return_value.start.assert_called_once()
        MockServer.return_value.start.assert_called_once()
        MockServer.return_value.stop.assert_called_once()
        MockDiscovery.return_value.stop.assert_called_once()

    def test_main_server_mode_with_daemon_flag(self):
        """Run main with server mode and the daemon flag."""
        with patch(
            "sys.argv",
            ["shatranj", "--server", "--daemon"],
        ):
            with patch(
                "shatranj.domain.network.DiscoveryServer"
            ) as MockDiscovery:
                with patch(
                    "shatranj.domain.network.GameServer"
                ) as MockServer:
                    with patch(
                        "shatranj.main.time.sleep",
                        side_effect=KeyboardInterrupt,
                    ):
                        with patch(
                            "sys.stdout",
                            new_callable=StringIO,
                        ) as mock_stdout:
                            result = main.main()

        assert result == 0
        assert mock_stdout.getvalue() == ""
        MockDiscovery.assert_called_once_with(
            "ShatranjServer",
            12345,
            main.VERSION,
        )
        MockServer.assert_called_once_with("ShatranjServer", 12345)

    def test_main_contest_mode(self, tmp_path):
        """Run main with contest mode."""
        save_file = tmp_path / "game.shj"
        save_file.write_text("[settings]\n[game]\nW\n...\n[history]\n")

        with patch("sys.argv", ["shatranj", "--contest", str(save_file)]):
            with patch(
                "shatranj.presentation.cli.cli.CLI._do_contest"
            ) as mock_contest:
                mock_contest.return_value = 0
                result = main.main()
                assert result == 0
                mock_contest.assert_called_once()

    def test_main_contest_mode_no_file(self):
        """Run main with contest mode but no file."""
        with patch("sys.argv", ["shatranj", "--contest"]):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                result = main.main()
                assert result == 1
                assert "requires a position file" in mock_stderr.getvalue()

    def test_main_contest_mode_forwards_cli_arguments_without_tmp_path(self):
        save_file = workspace_save_file(
            "contest_position.shj",
            "[settings]\n[game]\nW\n_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n_ _ _ _ _ _ _ _\n_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n_ _ _ _ _ _ _ _\n_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n[history]\n",
        )

        with (
            patch("sys.argv", ["shatranj", "--contest", str(save_file)]),
            patch("shatranj.presentation.cli.cli.CLI") as MockCLI,
        ):
            MockCLI.return_value._do_contest.return_value = 0
            result = main.main()

        assert result == 0
        MockCLI.assert_called_once_with(verbose=False, debug=False)
        MockCLI.return_value._do_contest.assert_called_once_with(
            path=str(save_file),
            algo="alphabeta",
            depth=3,
            scoring="advanced",
        )
        save_file.unlink(missing_ok=True)

    def test_main_invalid_ai_color(self):
        """Run main with invalid AI color."""
        with patch("sys.argv", ["shatranj", "--ai", "X"]):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                result = main.main()
                assert result == 1
                assert "invalid color" in mock_stderr.getvalue()

    def test_main_ai_all_players_sets_ai_vs_ai(self):
        with patch(
            "sys.argv",
            ["shatranj", "--ai", "A", "--ai-mode", "mcts", "--ai-depth", "12"],
        ):
            with patch("shatranj.main.ShatranjConfig") as MockConfig:
                mock_config = MockConfig.return_value
                mock_config.get_bool.return_value = False
                mock_config.get_int.return_value = 12
                mock_config.get_str.side_effect = lambda key: {
                    "ai-mode": "mcts",
                    "ai-scoring": "advanced",
                }.get(key, "advanced")
                with patch("shatranj.presentation.cli.cli.CLI") as MockCLI:
                    result = main.main()

        assert result == 0
        assert MockCLI.return_value._pending_new == [
            "ai-vs-ai",
            "mcts",
            "12",
            "advanced",
        ]

    def test_main_invalid_ai_algorithm(self):
        """Run main with invalid AI algorithm."""
        args = ["shatranj", "--ai", "B", "--ai-mode", "invalid"]
        with patch("sys.argv", args):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                result = main.main()
                assert result == 1
                assert "unknown algorithm" in mock_stderr.getvalue()

    def test_main_invalid_scoring(self):
        """Run main with invalid scoring function."""
        with patch(
            "sys.argv", ["shatranj", "--ai", "B", "--ai-scoring", "invalid"]
        ):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                result = main.main()
                assert result == 1
                assert "unknown scoring" in mock_stderr.getvalue()


class TestMainHelp:
    """Tests for help message."""

    def test_help_flag(self):
        """Show help with --help flag."""
        with patch("sys.argv", ["shatranj", "--help"]):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit) as exc:
                    main.main()
                assert exc.value.code == 0
                assert "usage:" in mock_stdout.getvalue()

    def test_help_mentions_extended_ai_options(self):
        parser = main.build_argument_parser()
        help_text = parser.format_help()

        assert "--ai-time" in help_text
        assert "--ai-minimax-depth" in help_text
        assert "--ai-minimax-scoring" in help_text
        assert "--ai-mcts-selection" in help_text


class TestMainBlitz:
    """Tests for blitz mode."""

    def test_main_blitz(self):
        """Run main with blitz mode."""
        with patch("sys.argv", ["shatranj", "--blitz", "--time", "15"]):
            with patch("shatranj.main.ShatranjConfig") as MockConfig:
                mock_config = MockConfig.return_value
                mock_config.get_bool.return_value = True
                mock_config.get_int.return_value = 15
                with patch(
                    "shatranj.presentation.cli.cli.CLI"
                ) as MockCLI:
                    mock_cli = MockCLI.return_value
                    mock_cli.run.return_value = 0
                    result = main.main()
                    assert result == 0
                    MockCLI.assert_called_once_with(
                        verbose=True,
                        debug=True,
                        blitz=True,
                        blitz_time_minutes=15,
                    )

    def test_main_blitz_without_time(self):
        """Run main with blitz mode default time."""
        with patch("sys.argv", ["shatranj", "--blitz"]):
            with patch("shatranj.main.ShatranjConfig") as MockConfig:
                mock_config = MockConfig.return_value
                mock_config.get_bool.return_value = True
                mock_config.get_int.return_value = 30
                with patch(
                    "shatranj.presentation.cli.cli.CLI"
                ) as MockCLI:
                    mock_cli = MockCLI.return_value
                    mock_cli.run.return_value = 0
                    result = main.main()
                    assert result == 0
                    MockCLI.assert_called_once_with(
                        verbose=True,
                        debug=True,
                        blitz=True,
                        blitz_time_minutes=30,
                    )

    def test_main_time_without_blitz_warning(self):
        """Show warning when --time is used without --blitz."""
        with patch("sys.argv", ["shatranj", "--time", "10"]):
            with patch("shatranj.main.ShatranjConfig") as MockConfig:
                mock_config = MockConfig.return_value
                mock_config.get_bool.return_value = False
                mock_config.get_int.return_value = 30
                with patch(
                    "sys.stderr", new_callable=StringIO
                ) as mock_stderr:
                    with patch(
                        "shatranj.presentation.cli.cli.CLI.run"
                    ) as mock_cli_run:
                        mock_cli_run.return_value = 0
                        result = main.main()
                        assert result == 0
                        assert "Warning" in mock_stderr.getvalue()


class TestMainAI:
    """Tests for AI mode."""

    def test_main_ai_white_minimax(self):
        """Run main with AI playing white using minimax."""
        with patch(
            "sys.argv", ["shatranj", "--ai", "W", "--ai-mode", "minimax"]
        ):
            with patch("shatranj.main.ShatranjConfig") as MockConfig:
                mock_config = MockConfig.return_value
                mock_config.get_bool.return_value = False
                mock_config.get_int.return_value = 3
                mock_config.get_str.side_effect = lambda key: {
                    "ai-mode": "minimax",
                    "ai-depth": 3,
                    "ai-scoring": "advanced"
                }.get(key, "advanced")
                with patch(
                    "shatranj.presentation.cli.cli.CLI"
                ) as MockCLI:
                    mock_cli = MockCLI.return_value
                    mock_cli.run.return_value = 0
                    result = main.main()
                    assert result == 0
                    expected = ["ai", "white", "minimax", "3", "advanced"]
                    assert mock_cli._pending_new == expected

    def test_main_ai_black_alphabeta(self):
        """Run main with AI playing black using alphabeta."""
        with patch(
            "sys.argv", ["shatranj", "--ai", "B", "--ai-mode", "alphabeta"]
        ):
            with patch("shatranj.main.ShatranjConfig") as MockConfig:
                mock_config = MockConfig.return_value
                mock_config.get_bool.return_value = False
                mock_config.get_int.return_value = 4
                mock_config.get_str.side_effect = lambda key: {
                    "ai-mode": "alphabeta",
                    "ai-depth": 4,
                    "ai-scoring": "advanced"
                }.get(key, "advanced")
                with patch(
                    "shatranj.presentation.cli.cli.CLI"
                ) as MockCLI:
                    mock_cli = MockCLI.return_value
                    mock_cli.run.return_value = 0
                    result = main.main()
                    assert result == 0
                    expected = ["ai", "black", "alphabeta", "4", "advanced"]
                    assert mock_cli._pending_new == expected

    def test_main_ai_mcts(self):
        """Run main with MCTS AI."""
        with patch(
            "sys.argv", ["shatranj", "--ai", "B", "--ai-mode", "mcts"]
        ):
            with patch("shatranj.main.ShatranjConfig") as MockConfig:
                mock_config = MockConfig.return_value
                mock_config.get_bool.return_value = False
                mock_config.get_int.return_value = 100
                mock_config.get_str.side_effect = lambda key: {
                    "ai-mode": "mcts",
                    "ai-depth": 100,
                    "ai-scoring": "advanced"
                }.get(key, "advanced")
                with patch(
                    "shatranj.presentation.cli.cli.CLI"
                ) as MockCLI:
                    mock_cli = MockCLI.return_value
                    mock_cli.run.return_value = 0
                    result = main.main()
                    assert result == 0
                    expected = ["ai", "black", "mcts", "100", "advanced"]
                    assert mock_cli._pending_new == expected

    def test_main_ai_custom_depth(self):
        """Run main with custom AI depth."""
        with patch(
            "sys.argv", ["shatranj", "--ai", "W", "--ai-depth", "6"]
        ):
            with patch("shatranj.main.ShatranjConfig") as MockConfig:
                mock_config = MockConfig.return_value
                mock_config.get_bool.return_value = False
                mock_config.get_int.return_value = 6
                mock_config.get_str.side_effect = lambda key: {
                    "ai-mode": "alphabeta",
                    "ai-depth": 6,
                    "ai-scoring": "advanced"
                }.get(key, "advanced")
                with patch(
                    "shatranj.presentation.cli.cli.CLI"
                ) as MockCLI:
                    mock_cli = MockCLI.return_value
                    mock_cli.run.return_value = 0
                    result = main.main()
                    assert result == 0
                    expected = ["ai", "white", "alphabeta", "6", "advanced"]
                    assert mock_cli._pending_new == expected

    def test_main_ai_custom_scoring(self):
        """Run main with custom scoring."""
        with patch(
            "sys.argv", ["shatranj", "--ai", "B", "--ai-scoring", "material"]
        ):
            with patch("shatranj.main.ShatranjConfig") as MockConfig:
                mock_config = MockConfig.return_value
                mock_config.get_bool.return_value = False
                mock_config.get_int.return_value = 4
                mock_config.get_str.side_effect = lambda key: {
                    "ai-mode": "alphabeta",
                    "ai-depth": 4,
                    "ai-scoring": "material"
                }.get(key, "material")
                with patch(
                    "shatranj.presentation.cli.cli.CLI"
                ) as MockCLI:
                    mock_cli = MockCLI.return_value
                    mock_cli.run.return_value = 0
                    result = main.main()
                    assert result == 0
                    expected = ["ai", "black", "alphabeta", "4", "material"]
                    assert mock_cli._pending_new == expected

    def test_main_ai_iterative_uses_configured_depth(self):
        with patch(
            "sys.argv", ["shatranj", "--ai", "W", "--ai-mode", "iterative"]
        ):
            with patch("shatranj.main.ShatranjConfig") as MockConfig:
                mock_config = MockConfig.return_value
                mock_config.get_bool.return_value = False
                mock_config.get_int.return_value = 7
                mock_config.get_str.side_effect = lambda key: {
                    "ai-mode": "iterative",
                    "ai-scoring": "advanced",
                }.get(key, "advanced")
                with patch("shatranj.presentation.cli.cli.CLI") as MockCLI:
                    result = main.main()

        assert result == 0
        assert MockCLI.return_value._pending_new == [
            "ai",
            "white",
            "iterative",
            "7",
            "advanced",
        ]

    def test_main_ai_minimax_uses_configured_depth(self):
        with patch(
            "sys.argv", ["shatranj", "--ai", "B", "--ai-mode", "minimax"]
        ):
            with patch("shatranj.main.ShatranjConfig") as MockConfig:
                mock_config = MockConfig.return_value
                mock_config.get_bool.return_value = False
                mock_config.get_int.return_value = 2
                mock_config.get_str.side_effect = lambda key: {
                    "ai-mode": "minimax",
                    "ai-scoring": "advanced",
                }.get(key, "advanced")
                with patch("shatranj.presentation.cli.cli.CLI") as MockCLI:
                    result = main.main()

        assert result == 0
        assert MockCLI.return_value._pending_new == [
            "ai",
            "black",
            "minimax",
            "2",
            "advanced",
        ]


class TestMainVerboseDebug:
    """Tests for verbose and debug flags."""

    def test_main_verbose(self):
        """Run main with verbose flag."""
        with patch("sys.argv", ["shatranj", "--verbose"]):
            with patch("shatranj.main.ShatranjConfig") as MockConfig:
                mock_config = MockConfig.return_value
                mock_config.get_int.return_value = 30

                def get_bool_side_effect(key):
                    if key == "verbose":
                        return True
                    return False

                mock_config.get_bool.side_effect = get_bool_side_effect
                with patch(
                    "shatranj.presentation.cli.cli.CLI"
                ) as MockCLI:
                    mock_cli = MockCLI.return_value
                    mock_cli.run.return_value = 0
                    result = main.main()
                    assert result == 0
                    MockCLI.assert_called_once_with(
                        verbose=True,
                        debug=False,
                        blitz=False,
                        blitz_time_minutes=30,
                    )

    def test_main_debug(self):
        """Run main with debug flag."""
        with patch("sys.argv", ["shatranj", "--debug"]):
            with patch("shatranj.main.ShatranjConfig") as MockConfig:
                mock_config = MockConfig.return_value
                mock_config.get_int.return_value = 30

                def get_bool_side_effect(key):
                    if key == "debug":
                        return True
                    return False

                mock_config.get_bool.side_effect = get_bool_side_effect
                with patch(
                    "shatranj.presentation.cli.cli.CLI"
                ) as MockCLI:
                    mock_cli = MockCLI.return_value
                    mock_cli.run.return_value = 0
                    result = main.main()
                    assert result == 0
                    MockCLI.assert_called_once_with(
                        verbose=False,
                        debug=True,
                        blitz=False,
                        blitz_time_minutes=30,
                    )

    def test_main_verbose_debug(self):
        """Run main with both verbose and debug."""
        with patch("sys.argv", ["shatranj", "--verbose", "--debug"]):
            with patch("shatranj.main.ShatranjConfig") as MockConfig:
                mock_config = MockConfig.return_value
                mock_config.get_int.return_value = 30

                def get_bool_side_effect(key):
                    if key in ("verbose", "debug"):
                        return True
                    return False

                mock_config.get_bool.side_effect = get_bool_side_effect
                with patch(
                    "shatranj.presentation.cli.cli.CLI"
                ) as MockCLI:
                    mock_cli = MockCLI.return_value
                    mock_cli.run.return_value = 0
                    result = main.main()
                    assert result == 0
                    MockCLI.assert_called_once_with(
                        verbose=True,
                        debug=True,
                        blitz=False,
                        blitz_time_minutes=30,
                    )


class TestMainLoadSave:
    """Tests for loading and saving games."""

    def test_main_load_file(self, tmp_path):
        """Run main with a save file to load."""
        save_file = tmp_path / "game.shj"
        save_file.write_text("[settings]\n[game]\nW\n...\n[history]\n")

        with patch("sys.argv", ["shatranj", str(save_file)]):
            with patch("shatranj.main.ShatranjConfig") as MockConfig:
                mock_config = MockConfig.return_value
                mock_config.get_bool.return_value = False
                with patch(
                    "shatranj.presentation.cli.cli.CLI"
                ) as MockCLI:
                    mock_cli = MockCLI.return_value
                    mock_cli.run.return_value = 0
                    result = main.main()
                    assert result == 0
                    mock_cli._do_load.assert_called_once_with(
                        [str(save_file)]
                    )


class TestMainVersion:
    """Tests for version flag."""

    def test_version_flag(self):
        """Show version with -V flag."""
        with patch("sys.argv", ["shatranj", "-V"]):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit) as exc:
                    main.main()
                assert exc.value.code == 0
                assert "0.4.0" in mock_stdout.getvalue()


class TestMainErrorHandling:
    """Tests for error handling."""

    def test_main_gui_not_available(self):
        """Handle GUI not available gracefully."""
        with patch("sys.argv", ["shatranj", "--gui"]):
            with patch("shatranj.main.ShatranjConfig") as MockConfig:
                mock_config = MockConfig.return_value
                mock_config.get_bool.return_value = False
                with patch(
                    "shatranj.presentation.gui.app.run_gui",
                    side_effect=ModuleNotFoundError
                ):
                    with patch(
                        "sys.stderr", new_callable=StringIO
                    ) as mock_stderr:
                        result = main.main()
                        assert result == 1
                        assert "GUI requires GTK" in mock_stderr.getvalue()
