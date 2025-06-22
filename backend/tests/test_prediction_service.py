# Backend/tests/test_prediction_service.py

import unittest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
import math

# Importa la clase que vamos a probar
from services.prediction_service import PredictionService 

# Importa los modelos para asegurarte de que están accesibles (si los vas a mockear o no)
from models import exponential_model, gompertz_model 

# Para simular la sesión de base de datos
class MockSession:
    def add(self, obj):
        pass
    def commit(self):
        pass
    def rollback(self):
        pass
    def close(self):
        pass

# Para simular un objeto de medición de tumor
class MockTumorMeasurement:
    def __init__(self, size_cm3, measurement_date):
        self.size_cm3 = size_cm3
        self.measurement_date = measurement_date

# Para simular un objeto de paciente
class MockPatient:
    def __init__(self, id, identification_number, name, date_of_birth):
        self.id = id
        self.identification_number = identification_number
        self.name = name
        self.date_of_birth = date_of_birth
        self.tumor_measurements = [] # Inicialmente vacío para pruebas


class TestPredictionService(unittest.TestCase):

    def setUp(self):
        """
        Configura el entorno para cada prueba.
        Usaremos mocks para la base de datos para que las pruebas sean rápidas e independientes.
        """
        self.mock_db_session = MockSession()
        self.service = PredictionService(self.mock_db_session)

        # Mockear PatientDataManager para controlar su comportamiento
        self.service.patient_data_manager = MagicMock()

        # Mockear los modelos para que no necesitemos cálculos reales aquí
        # Esto es clave para las pruebas unitarias: probar UNA unidad aislada
        exponential_model.calculate_time_to_threshold_exponential = MagicMock(return_value=100)
        exponential_model.generate_exponential_curve_points = MagicMock(return_value=[[0,1],[100,10]])
        exponential_model.calculate_confidence_interval_exponential = MagicMock(return_value=(90, 110))

        gompertz_model.calculate_time_to_threshold_gompertz = MagicMock(return_value=150)
        gompertz_model.generate_gompertz_curve_points = MagicMock(return_value=[[0,1],[150,10]])
        gompertz_model.calculate_confidence_interval_gompertz = MagicMock(return_value=(140, 160))


    def test_calculate_age(self):
        """Prueba el cálculo de la edad."""
        dob = date(1990, 5, 15)
        # Usamos patch para simular la fecha actual para que la prueba sea reproducible
        with patch('services.prediction_service.date') as mock_date:
            mock_date.today.return_value = date(2024, 5, 15)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw) # Para que date() funcione normalmente
            self.assertEqual(self.service._calculate_age(dob), 34)

        with patch('services.prediction_service.date') as mock_date:
            mock_date.today.return_value = date(2024, 5, 14) # Antes del cumpleaños
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
            self.assertEqual(self.service._calculate_age(dob), 33)

    def test_determine_simplified_cancer_stage(self):
        """Prueba la determinación de la etapa del cáncer."""
        self.assertEqual(self.service._determine_simplified_cancer_stage(1.5), "Etapa I")
        self.assertEqual(self.service._determine_simplified_cancer_stage(3.0), "Etapa II")
        self.assertEqual(self.service._determine_simplified_cancer_stage(7.0), "Etapa III")
        self.assertEqual(self.service._determine_simplified_cancer_stage(12.0), "Etapa IV")
        self.assertEqual(self.service._determine_simplified_cancer_stage(0.1), "Etapa I") # Caso mínimo
        self.assertEqual(self.service._determine_simplified_cancer_stage(20.0), "Etapa IV") # Caso máximo

    def test_get_bibliographic_parameters_default(self):
        """Prueba la obtención de parámetros bibliográficos por defecto."""
        patient_data = {'tipo_cancer': 'Cáncer de Mama', 'age': 30}
        params = self.service._get_bibliographic_parameters(patient_data)
        self.assertAlmostEqual(params['r'], 0.0042) # Valor por defecto sin ajustes
        self.assertEqual(params['K'], 20.0)

    def test_get_bibliographic_parameters_with_adjustments(self):
        """Prueba la obtención de parámetros con ajustes por factores."""
        patient_data = {
            'tipo_cancer': 'Cáncer de Mama',
            'subtipo_molecular': 'Triple Negativo',
            'grado_histopatologico': 'Grado 3',
            'age': 40, # Joven
            'metastasis': 'Si',
            'er_pr': 'Negativo',
            'her2': 'Positivo',
            'simplified_cancer_stage': 'Etapa IV' # Para el ajuste de r en etapa IV
        }
        params = self.service._get_bibliographic_parameters(patient_data)

        # r_base de subtipo: 0.0067
        # r_base ajustada por grado 3: 0.0036 (esto sobrescribe el subtipo si el código lo hace así)
        # ACTAULIZACIÓN: Mi código de _get_bibliographic_parameters prioriza y sobreescribe, no multiplica factores.
        # Vamos a ajustar los valores esperados según la lógica de sobrescritura.
        # La lógica actual es: default -> subtipo -> grado. Luego aplica factores multiplicativos.

        # r_inicial (desde Grado 3): 0.0036
        # Ajuste por Edad Joven: 0.0036 * 1.1 = 0.00396
        # Ajuste por Metástasis: 0.00396 * 1.3 = 0.005148
        # Ajuste por HER2 Positivo: 0.005148 * 1.1 = 0.0056628
        # Ajuste por Etapa IV: 0.0056628 * 1.2 = 0.00679536

        self.assertAlmostEqual(params['r'], 0.00679536, places=8)
        self.assertEqual(params['K'], 20.0)


    def test_calculate_empirical_r_growth(self):
        """Prueba el cálculo de r empírica para crecimiento."""
        T_anterior = 1.0
        T_actual = 2.0
        time_diff_days = 100
        # r = ln(2/1) / 100 = ln(2) / 100
        expected_r = math.log(2) / 100
        self.assertAlmostEqual(self.service._calculate_empirical_r(T_anterior, T_actual, time_diff_days), expected_r)

    def test_calculate_empirical_r_regression(self):
        """Prueba el cálculo de r empírica para regresión."""
        T_anterior = 2.0
        T_actual = 1.0
        time_diff_days = 100
        # r = ln(1/2) / 100 = ln(0.5) / 100
        expected_r = math.log(0.5) / 100
        self.assertAlmostEqual(self.service._calculate_empirical_r(T_anterior, T_actual, time_diff_days), expected_r)

    def test_calculate_empirical_r_total_regression(self):
        """Prueba el cálculo de r empírica cuando el tumor desaparece."""
        T_anterior = 5.0
        T_actual = 0.0 # Tumor disappeared
        time_diff_days = 50
        # En este caso, esperamos el valor simbólico de regresión severa.
        self.assertEqual(self.service._calculate_empirical_r(T_anterior, T_actual, time_diff_days), -100.0)

    def test_predict_new_patient(self):
        """Prueba la predicción para un nuevo paciente (solo r bibliográfica)."""
        self.service.patient_data_manager.get_patient_by_identification_number.return_value = None
        self.service.patient_data_manager.create_patient.return_value = MockPatient(
            id=1, identification_number="ID123", name="Test Patient", date_of_birth=date(1990,1,1)
        )

        result = self.service.predict(
            identification_number="ID123",
            current_tumor_size=1.0,
            current_measurement_date=date(2024, 1, 1),
            patient_name="Test Patient",
            date_of_birth=date(1990, 1, 1),
            T_critical=10.0
        )

        self.assertEqual(result['status'], 'ok')
        self.assertIn("Utilizando tasa de crecimiento **bibliográfica**", result['message'])
        self.assertIsNotNone(result['model_results']['exponential']['prediction_days'])
        self.assertIsNone(result['parameters_used_for_prediction'].get('r_empirical_calculated'))
        self.assertTrue(result['patient_info']['is_new_patient'])

    def test_predict_existing_patient_growth(self):
        """Prueba la predicción para un paciente existente con crecimiento (r empírica)."""
        mock_patient = MockPatient(id=1, identification_number="ID456", name="Existing Patient", date_of_birth=date(1980,1,1))
        self.service.patient_data_manager.get_patient_by_identification_number.return_value = mock_patient

        # Simulamos mediciones anteriores
        self.service.patient_data_manager.get_all_tumor_measurements_for_patient.return_value = [
            MockTumorMeasurement(size_cm3=1.0, measurement_date=date(2023, 1, 1)),
            MockTumorMeasurement(size_cm3=2.0, measurement_date=date(2024, 1, 1)) # Esta es la "anterior" a la actual
        ]

        result = self.service.predict(
            identification_number="ID456",
            current_tumor_size=3.0, # Tamaño actual, mayor que el anterior (2.0)
            current_measurement_date=date(2024, 6, 1),
            T_critical=10.0
        )

        self.assertEqual(result['status'], 'ok')
        self.assertIn("Utilizando tasa de crecimiento **empírica**", result['message'])
        self.assertIsNotNone(result['parameters_used_for_prediction']['r_empirical_calculated'])
        self.assertGreater(result['parameters_used_for_prediction']['r_empirical_calculated'], 0)
        self.assertIsNotNone(result['model_results']['exponential']['prediction_days'])
        self.assertFalse(result['patient_info']['is_new_patient'])

    def test_predict_existing_patient_regression(self):
        """Prueba la predicción para un paciente existente con regresión."""
        mock_patient = MockPatient(id=1, identification_number="ID789", name="Regressing Patient", date_of_birth=date(1970,1,1))
        self.service.patient_data_manager.get_patient_by_identification_number.return_value = mock_patient

        self.service.patient_data_manager.get_all_tumor_measurements_for_patient.return_value = [
            MockTumorMeasurement(size_cm3=5.0, measurement_date=date(2023, 1, 1)),
            MockTumorMeasurement(size_cm3=4.0, measurement_date=date(2024, 1, 1)) # Esta es la "anterior" a la actual
        ]

        result = self.service.predict(
            identification_number="ID789",
            current_tumor_size=2.0, # Tamaño actual, menor que el anterior (4.0)
            current_measurement_date=date(2024, 6, 1),
            T_critical=10.0
        )

        self.assertEqual(result['status'], 'tumor_regressing')
        self.assertIn("¡El tumor está disminuyendo!", result['message'])
        self.assertLess(result['parameters_used_for_prediction']['r_final'], 0) # r_final debe ser negativa
        self.assertIsNone(result['model_results']['exponential']['prediction_days']) # No debe haber predicción de días
        self.assertIsNotNone(result['model_results']['exponential']['curve_data']) # Pero sí puede haber data de curva
        self.assertFalse(result['patient_info']['is_new_patient'])