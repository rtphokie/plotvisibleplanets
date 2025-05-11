import datetime
import os
import uuid
from pprint import pprint
import unittest
from whatsup import whatsup


class MyTestCase(unittest.TestCase):
    def test_evening(self):
        filename = f'test_evening_{uuid.uuid4().hex}.png'
        result, maxalt, _, _, _ = whatsup(sky='dusk', date=datetime.datetime(2024, 1, 3), verbose=False, minutes=30,
                                          tzs='US/Eastern', lat=38.91, lon=-77.04, location='Washington DC',
                                          filename=filename)
        self.assertTrue(os.path.isfile(filename), f'{filename} not generated')
        # os.remove(filename)  # the above should short circuit
        self.assertAlmostEqual(maxalt, 52, places=0)
        self.assertAlmostEqual(result['Sun']['altitude'], -6.2, places=1)
        self.assertAlmostEqual(result['Sun']['azimuth'], 245.57, places=1)

    def test_morning(self):
        filename = f'test_morning_{uuid.uuid4().hex}.png'
        result, maxalt, _, _, _ = whatsup(sky='dawn', date=datetime.datetime(2024, 1, 3), verbose=False,
                                          filename=filename)
        self.assertTrue(os.path.isfile(filename), f'{filename} not generated')
        os.remove(filename)  # the above should short circuit
        self.assertAlmostEqual(maxalt, 48, places=0)
        self.assertAlmostEqual(result['Sun']['altitude'], -11.7, places=1)
        self.assertAlmostEqual(result['Sun']['azimuth'], 110, places=1)

    def test_evening_raleigh_2024_06_03(self):
        filename = f'test_morning_{uuid.uuid4().hex}.png'
        result, maxalt, _, _, _ = whatsup(sky='dawn', lat=35.5, lon=-78.8, location='Raleigh, NC',
                                          date=datetime.datetime(2024, 6, 3), verbose=False, minutes=30,
                                          filename=filename)
        self.assertTrue(os.path.isfile(filename), f'{filename} not generated')
        # os.remove(filename) # the above should short circuit
        self.assertAlmostEqual(maxalt, 52, places=0)
        self.assertAlmostEqual(result['Sun']['altitude'], -6.2, places=1)
        self.assertAlmostEqual(result['Sun']['azimuth'], 245.57, places=1)


if __name__ == '__main__':
    unittest.main()
