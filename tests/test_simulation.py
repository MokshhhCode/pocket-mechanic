import unittest
from modules.sensor import SimulatedSensorProvider, HardwareSensorProvider

class TestSensorSimulationAndProviders(unittest.TestCase):
    def setUp(self):
        self.sim = SimulatedSensorProvider()
        self.hw = HardwareSensorProvider()

    def test_regular_vs_intense_simulation(self):
        specs = {'displacement_cc': 350.0, 'cooling_type': 'Air', 'final_drive_type': 'Chain'}
        reg = self.sim.get_telemetry_packet(1, specs, intensity='Regular')
        med = self.sim.get_telemetry_packet(1, specs, intensity='Medium')
        inte = self.sim.get_telemetry_packet(1, specs, intensity='Intense')

        self.assertEqual(reg['source_type'], 'SIMULATED')
        self.assertEqual(reg['status'], 'ONLINE')
        self.assertEqual(len(reg['anomalies']), 0)

        # Intense mode must induce severe faults
        self.assertEqual(inte['status'], 'CRITICAL_FAULT')
        self.assertTrue(len(inte['anomalies']) >= 3)
        self.assertGreater(inte['readings']['ENG_TEMP'], reg['readings']['ENG_TEMP'])
        self.assertLess(inte['readings']['BAT_VOLT'], 12.0)
        self.assertLess(inte['readings']['BRAKE_PAD_WEAR'], 2.0)

    def test_hardware_sensor_provider_integrity(self):
        # When physical hardware is not attached, provider must return DISCONNECTED with NO fabricated data
        status = self.hw.get_provider_status()
        packet = self.hw.get_telemetry_packet(1)

        self.assertEqual(status['mode'], 'HARDWARE')
        self.assertTrue(self.hw.is_hardware())
        if not status['connected']:
            self.assertEqual(packet['status'], 'DISCONNECTED')
            self.assertIsNone(packet['readings'], "Hardware provider must NEVER fabricate data when offline!")

if __name__ == '__main__':
    unittest.main()
