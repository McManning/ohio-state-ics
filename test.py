import unittest

from build import parse_date

class TestParseDate(unittest.TestCase):
  def test_parse_date(self):
    self.assertEqual(parse_date('Mar 14-18 (M-F)', 2023), ['2023-03-14', '2023-03-18'])
    self.assertEqual(parse_date('TBA', 2023), [])
    self.assertEqual(parse_date('March 15 (W)', 2023), ['2023-03-15', '2023-03-15'])
    self.assertEqual(parse_date('Apr 26-May 2 (W-T)', 2023), ['2023-04-26', '2023-05-02'])
    self.assertEqual(parse_date('Jul 28-30 (M-W)', 2023), ['2023-07-28', '2023-07-30'])
    self.assertEqual(parse_date('mar 14-18 (M-F)', 2023), ['2023-03-14', '2023-03-18'])

    self.assertEqual(parse_date('march 15 (W)', 2023), ['2023-03-15', '2023-03-15'])
    self.assertEqual(parse_date('apr 26-may 2 (W-T)', 2023), ['2023-04-26', '2023-05-02'])
    self.assertEqual(parse_date('jul 28-30 (M-W)', 2023), ['2023-07-28', '2023-07-30'])
    self.assertEqual(parse_date('Mar 14 (X)', 2023), ['2023-03-14', '2023-03-14'])
    self.assertEqual(parse_date('Apr 26-May 2 (Y-Z)', 2023), ['2023-04-26', '2023-05-02'])


if __name__ == '__main__':
  unittest.main()
