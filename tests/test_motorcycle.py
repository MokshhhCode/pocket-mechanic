import unittest
from database.connection import get_db_connection

class TestMotorcycleMasterDatabase(unittest.TestCase):
    def test_28_manufacturers_seeded(self):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as cnt FROM manufacturers")
                res = cursor.fetchone()
                self.assertEqual(res['cnt'], 28)
        finally:
            conn.close()

    def test_component_applicability_rules(self):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 1. Royal Enfield Classic 350 is Air/Oil cooled: Coolant must be NOT applicable
                cursor.execute(
                    """
                    SELECT mca.is_applicable FROM model_component_applicability mca
                    JOIN motorcycle_variants mv ON mca.variant_id = mv.variant_id
                    JOIN motorcycle_models mm ON mv.model_id = mm.model_id
                    JOIN component_catalogue c ON mca.component_id = c.component_id
                    WHERE mm.name = 'Classic 350' AND c.component_code = 'ENGINE_COOLANT'
                    """
                )
                re_cool = cursor.fetchone()
                self.assertEqual(re_cool['is_applicable'], 0, "Air-cooled motorcycle must not have coolant check!")

                # 2. BMW R 1250 GS is Liquid-cooled: Coolant MUST be applicable
                cursor.execute(
                    """
                    SELECT mca.is_applicable FROM model_component_applicability mca
                    JOIN motorcycle_variants mv ON mca.variant_id = mv.variant_id
                    JOIN motorcycle_models mm ON mv.model_id = mm.model_id
                    JOIN component_catalogue c ON mca.component_id = c.component_id
                    WHERE mm.name = 'R 1250 GS' AND c.component_code = 'ENGINE_COOLANT'
                    """
                )
                bmw_cool = cursor.fetchone()
                self.assertEqual(bmw_cool['is_applicable'], 1, "Liquid-cooled BMW must have coolant check!")

                # 3. Harley Fat Boy 114 has Belt Drive: Drive chain must be overridden with Belt
                cursor.execute(
                    """
                    SELECT mca.display_name_override, mca.rule_condition FROM model_component_applicability mca
                    JOIN motorcycle_variants mv ON mca.variant_id = mv.variant_id
                    JOIN motorcycle_models mm ON mv.model_id = mm.model_id
                    JOIN component_catalogue c ON mca.component_id = c.component_id
                    WHERE mm.name = 'Fat Boy 114' AND c.component_code = 'DRIVE_CHAIN'
                    """
                )
                hd_drive = cursor.fetchone()
                self.assertIn("Belt", hd_drive['display_name_override'])

                # 4. Bajaj Pulsar 150 has Rear Drum: Brake lining must be overridden with Drum Brake Shoe
                cursor.execute(
                    """
                    SELECT mca.display_name_override FROM model_component_applicability mca
                    JOIN motorcycle_variants mv ON mca.variant_id = mv.variant_id
                    JOIN motorcycle_models mm ON mv.model_id = mm.model_id
                    JOIN component_catalogue c ON mca.component_id = c.component_id
                    WHERE mm.name = 'Pulsar 150' AND c.component_code = 'REAR_BRAKE_LINING'
                    """
                )
                pulsar_brakes = cursor.fetchone()
                self.assertIn("Drum Brake Shoe", pulsar_brakes['display_name_override'])
        finally:
            conn.close()

if __name__ == '__main__':
    unittest.main()
