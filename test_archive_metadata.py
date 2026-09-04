import unittest
from archive_metadata import archive_identity, entry_metadata, pgn_metadata, render_metadata


class MetadataTests(unittest.TestCase):
    def test_supported_source_names_keep_early_and_late_distinct(self):
        self.assertEqual(archive_identity('240102a-titled-tuesday.pgn'), ('2024-01-02', 'a'))
        self.assertEqual(archive_identity('titled-tuesday-2024-01-02b.zip'), ('2024-01-02', 'b'))
        self.assertEqual(archive_identity('2026-titled-tuesday-blitz-august-25.pgn'), ('2026-08-25', ''))
        self.assertEqual(archive_identity('2024-titled-tuesday-blitz-january-02-late.pgn'), ('2024-01-02', 'b'))
        self.assertEqual(archive_identity('cc_titled-tuesday_240102a.zip'), ('2024-01-02', 'a'))
        self.assertEqual(archive_identity('cc_titled-tuesday_210504.pgn'), ('2021-05-04', ''))

    def test_event_identity_uses_the_event_filename(self):
        # Game Date tags can cross midnight or reflect later source corrections.
        self.assertEqual(archive_identity('260825-titled-tuesday.pgn')[0], '2026-08-25')

    def test_invalid_dates_and_unrelated_filenames_fail(self):
        for filename in ('260230-titled-tuesday.pgn', '../260106-titled-tuesday.pgn', 'tournament.pgn'):
            with self.assertRaises(ValueError):
                archive_identity(filename)

    def test_header_only_stubs_cannot_be_imported(self):
        with self.assertRaises(ValueError):
            pgn_metadata(b'[Event "Titled Tuesday"]\n', strict=True)

    def test_zero_move_results_are_retained_and_eventdate_is_not_counted(self):
        content = b'[Event "Titled Tuesday"]\n[EventDate "2026.08.25"]\n[White "A"]\n[Black "B"]\n[Result "1-0"]\n\n1-0\n'
        self.assertEqual(pgn_metadata(content, strict=True), ('Titled Tuesday', 1))

    def test_metadata_links_use_forward_slashes(self):
        entry = entry_metadata('cc_titled-tuesday_240102a.zip', 'cc_titled-tuesday_240102a.pgn', 'Titled Tuesday', 10, 'a' * 64)
        self.assertEqual(entry['session'], 'early')
        self.assertIn('/2024/cc_titled-tuesday_240102a.zip', render_metadata([entry])['tt_links.txt'])
        self.assertNotIn('\\', entry['url'])


if __name__ == '__main__':
    unittest.main()
