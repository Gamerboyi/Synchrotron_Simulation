"""
Unit tests for the Particle class.

Validates energy/momentum calculations and conservation properties.
"""

import numpy as np
import pytest

from particle import Particle
from constants import PROTON_CHARGE, PROTON_MASS, C, EV_TO_JOULES
from physics import derivatives_particle
from integrators import rk4_step_particle


class TestParticleEnergy:
    """Tests for kinetic energy and momentum calculations."""

    def test_classical_energy(self):
        """Non-relativistic KE = ½mv² for a proton at 1% c."""
        v = 0.01 * C
        p = Particle(0.0, 5.0, v, 0.0, PROTON_CHARGE, PROTON_MASS)
        p.update_energy(relativistic=False)

        expected_joules = 0.5 * PROTON_MASS * v * v
        assert p.energy_joules == pytest.approx(expected_joules, rel=1e-10)
        assert p.energy_ev == pytest.approx(expected_joules / EV_TO_JOULES, rel=1e-10)

    def test_relativistic_momentum(self):
        """Relativistic momentum p = γmv for a proton at 50% c."""
        v = 0.5 * C
        p = Particle(0.0, 5.0, v, 0.0, PROTON_CHARGE, PROTON_MASS)
        gamma = 1.0 / np.sqrt(1.0 - 0.5**2)
        p.gamma = gamma
        p.update_energy(relativistic=True)

        expected_px = gamma * PROTON_MASS * v
        assert p.px == pytest.approx(expected_px, rel=1e-6)
        assert p.py == pytest.approx(0.0, abs=1e-30)
        assert p.p == pytest.approx(expected_px, rel=1e-6)


class TestEnergyConservation:
    """Tests for energy conservation in pure magnetic field (no RF)."""

    def test_energy_conserved_without_rf(self):
        """
        In a pure magnetic field (no RF, no focusing), kinetic energy
        must be conserved because magnetic force does no work.
        """
        Bz = 1.0
        dt = 1e-10
        steps = 5000

        v = 1e6  # 1 million m/s (non-relativistic)
        r_theory = (PROTON_MASS * v) / (PROTON_CHARGE * Bz)

        p = Particle(0.0, r_theory, v, 0.0, PROTON_CHARGE, PROTON_MASS)
        initial_energy = 0.5 * PROTON_MASS * v * v

        for _ in range(steps):
            rk4_step_particle(
                p, dt, derivatives_particle,
                Bz=Bz, relativistic=False,
                enable_rf_kick=False, enable_focusing=False,
            )

        final_speed_sq = p.vx**2 + p.vy**2
        final_energy = 0.5 * PROTON_MASS * final_speed_sq

        # Energy should be conserved within 0.1% over 5000 steps
        rel_error = abs(final_energy - initial_energy) / initial_energy
        assert rel_error < 0.001
