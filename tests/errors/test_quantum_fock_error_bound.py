import jax.numpy as jnp
import unittest
from qureed.errors import QuantumFockErrorBound
from qureed.simulation.simulation import Simulation


class TestQuantumFockErrorBound(unittest.TestCase):
    def setUp(self):
        Simulation().reset()

    def tearDown(self) -> None:
        Simulation().reset()

    def test_perfect_identity_channel(self) -> None:
        rho = jnp.array([[1.0, 0.0], [0.0, 0.0]])
        kraus_ops = [jnp.eye(2)]
        qerr = QuantumFockErrorBound()
        qerr.compute(rho, kraus_ops)
        self.assertEqual(qerr.error, 0)
        self.assertEqual(qerr.entanglement_error, 0)

    def test_pure_loss_channel(self) -> None:
        rho = jnp.array([[0.0, 0.0], [0.0, 1.0]])  # |1><1|
        eta = 0.7

        C0 = jnp.array([[1.0, 0.0], [0.0, jnp.sqrt(eta)]])
        C1 = jnp.array([[0.0, jnp.sqrt(1 - eta)], [0.0, 0.0]])

        kraus_ops = [C0, C1]
        qerr = QuantumFockErrorBound()
        qerr.compute(rho, kraus_ops)
        self.assertTrue(
            jnp.isclose(qerr.error, 0.0).item(),
            f"Got {qerr.error}, expected 0.0",
        )
        expected_fe = (
            jnp.abs(jnp.trace(rho @ C0)) ** 2
            + jnp.abs(jnp.trace(rho @ C1)) ** 2
        )
        self.assertTrue(
            jnp.isclose(1 - qerr.entanglement_error, expected_fe).item()
        )

        qerr = QuantumFockErrorBound()
        qerr.compute(rho, [C0])
        # expected_tr_error = jnp.trace(C1.conj().T @ C1 @ rho).real
        expected_tr_error = jnp.trace(C1 @ rho @ C1.conj().T).real
        expected_fe = jnp.abs(jnp.trace(rho @ C0)) ** 2
        self.assertTrue(
            jnp.isclose(qerr.error, expected_tr_error).item(),
            f"Got {qerr.error}, expected {expected_tr_error}",
        )
        self.assertTrue(
            jnp.isclose(1 - qerr.entanglement_error, expected_fe).item()
        )
