import numpy as np
from scipy.optimize import curve_fit
from datetime import date
from typing import List, Tuple, Dict, Any
import logging

#logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PredictionService:
    
    # --- 1. Definición de Modelos Matemáticos ---
    
    @staticmethod
    def model_exponential(t, V0, r):
        """Modelo Exponencial: V(t) = V0 * e^(r*t)"""
        return V0 * np.exp(np.clip(r * t, -100, 100))

    @staticmethod
    def model_gompertz(t, V0, r, K):
        """Modelo Gompertz: V(t) = K * exp(ln(V0/K) * exp(-r*t))"""
        if K <= 0 or V0 <= 0: return V0 
        term1 = np.log(V0 / K)
        term2 = np.exp(np.clip(-r * t, -100, 100))
        return K * np.exp(term1 * term2)

    # --- 2. Preparación de Datos ---

    def prepare_data(self, dates: List[date], sizes: List[float]) -> Tuple[np.ndarray, np.ndarray]:
        if not dates or not sizes:
            logger.warning("Intento de preparar datos con listas vacías.")
            return np.array([]), np.array([])
            
        start_date = min(dates)
        days_diff = np.array([(d - start_date).days for d in dates])
        sizes_arr = np.array(sizes)
        
        sorted_indices = np.argsort(days_diff)
        logger.info(f"Datos preparados: {len(sizes)} puntos de medición.")
        return days_diff[sorted_indices], sizes_arr[sorted_indices]

    # --- 3. Ajuste de Curvas (Regression) ---

    def fit_models(self, dates: List[date], sizes: List[float]):
        x_data, y_data = self.prepare_data(dates, sizes)
        
        # --- CORRECCIÓN CLAVE ---
        # Inicializamos la estructura SIEMPRE, para que nunca falten las llaves
        results = {
            "exponential": {"success": False, "error": "Datos insuficientes"},
            "gompertz": {"success": False, "error": "Datos insuficientes"},
            "data_points": len(x_data)
        }
        
        # Si hay menos de 2 puntos, devolvemos la estructura vacía (pero correcta)
        if len(x_data) < 2:
            logger.info("Menos de 2 puntos de datos. No se puede calcular tendencia.")
            return results

        logger.info(f"Iniciando ajuste de modelos para {len(x_data)} mediciones.")
        # Si hay suficientes datos, intentamos calcular...

        # --- Ajuste Exponencial ---
        try:
            initial_guess_exp = [y_data[0], 0.004] 
            params_exp, covariance_exp = curve_fit(
                self.model_exponential, 
                x_data, y_data, 
                p0=initial_guess_exp, 
                bounds=([0, 0], [np.inf, 1.0]),
                maxfev=5000
            )
            
            residuals = y_data - self.model_exponential(x_data, *params_exp)
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((y_data - np.mean(y_data))**2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

            logger.info(f"Modelo Exponencial convergido. R2: {r_squared:.4f}")

            results["exponential"] = {
                "success": True,
                "params": {"V0": params_exp[0], "r": params_exp[1]},
                "r_squared": r_squared
            }
        except Exception as e:
            logger.error(f"Fallo en ajuste Exponencial: {str(e)}")
            results["exponential"]["error"] = str(e)

        # --- Ajuste Gompertz ---
        try:
            # K debe ser al menos un 20% mayor que el tamaño actual más grande
            max_size = y_data.max()
            min_K = max_size * 1.2 
            # Límite superior teórico: 1000 cm3 (tumor gigante, para dar margen)
            initial_K = max(min_K, 100.0) 

            initial_guess_gom = [y_data[0], 0.004, initial_K]
            params_gom, covariance_gom = curve_fit(
                self.model_gompertz,
                x_data, y_data,
                p0=initial_guess_gom,
                bounds=([0, 0, max_size], [np.inf, 1.0, 5000]),
                maxfev=10000
            )

            residuals = y_data - self.model_gompertz(x_data, *params_gom)
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((y_data - np.mean(y_data))**2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

            logger.info(f"Modelo Gompertz convergido. R2: {r_squared:.4f}, K_est: {params_gom[2]:.2f}")

            results["gompertz"] = {
                "success": True,
                "params": {"V0": params_gom[0], "r": params_gom[1], "K": params_gom[2]},
                "r_squared": r_squared
            }
        except Exception as e:
            logger.error(f"Fallo en ajuste Gompertz: {str(e)}")
            results["gompertz"]["error"] = str(e)

        return results

    # --- 4. Proyección a Futuro ---
    
    def predict_future(self, model_results: Dict, days_ahead: int = 365):
        predictions = {}
        t_future = np.linspace(0, days_ahead, 100)
        
        # Ahora esto es seguro porque "exponential" siempre existe
        if model_results["exponential"]["success"]:
            p = model_results["exponential"]["params"]
            y_pred = self.model_exponential(t_future, p["V0"], p["r"])
            predictions["exponential"] = [{"day": t, "size": v} for t, v in zip(t_future, y_pred)]
            
        if model_results["gompertz"]["success"]:
            p = model_results["gompertz"]["params"]
            y_pred = self.model_gompertz(t_future, p["V0"], p["r"], p["K"])
            predictions["gompertz"] = [{"day": t, "size": v} for t, v in zip(t_future, y_pred)]
            
        return predictions