"""
Unit tests for the physics engine.

Validates electromagnetic force calculations, RF cavity behavior,
focusing field, and relativistic corrections against analytical expectations.
"""

import numpy as np
import pytest

from particle import Particle
from constants import PROTON_CHARGE, PROTON_MASS, C
from physics import (
    gamma_from_v,
    lorentz_acceleration_2d,
    rf_gap_kick,
    focusing_field,
)


class TestGammaFromV:
    """Tests for the Lorentz factor calculation."""

    def test_gamma_at_zero_velocity(self):
        """γ must equal 1.0 when v = 0 (rest frame)."""
        assert gamma_from_v(0.0, 0.0) == pytest.approx(1.0)

    def test_gamma_near_speed_of_light(self):
        """γ must be >> 1 when v approaches c."""
        vx = 0.99 * C
        gamma = gamma_from_v(vx, 0.0)
        expected = 1.0 / np.sqrt(1.0 - 0.99**2)
        assert gamma == pytest.approx(expected, rel=1e-6)
        assert gamma > 7.0  # γ ≈ 7.089 at 0.99c

    def test_gamma_symmetric_in_vx_vy(self):
        """γ depends only on |v|, not direction."""
        g1 = gamma_from_v(1e6, 0.0)
        g2 = gamma_from_v(0.0, 1e6)
        g3 = gamma_from_v(1e6 / np.sqrt(2), 1e6 / np.sqrt(2))
        assert g1 == pytest.approx(g2, rel=1e-10)
        assert g1 == pytest.approx(g3, rel=1e-10)


class TestRFGapKick:
    """Tests for the RF cavity spatial boundaries."""

    def test_rf_gap_only_fires_positive_x(self):
        """RF kick must return (0, 0) when x <= 0."""
        Ex, Ey = rf_gap_kick(x=-1.0, y=0.0, ring_radius=5.0, E0=5e4)
        assert Ex == 0.0
        assert Ey == 0.0

    def test_rf_gap_respects_halfwidth(self):
        """RF kick must return (0, 0) when |y| > gap_halfwidth."""
        Ex, Ey = rf_gap_kick(
            x=5.0, y=0.5, ring_radius=5.0, gap_halfwidth=0.10, E0=5e4
        )
        assert Ex == 0.0
        assert Ey == 0.0

    def test_rf_gap_fires_inside_region(self):
        """RF kick must produce a nonzero Ey inside the gap."""
        # Use omega=0 so sin(phi) = sin(0) = 0 → need phase offset
        Ex, Ey = rf_gap_kick(
            x=5.0, y=0.0, ring_radius=5.0,
            gap_halfwidth=0.10, E0=5e4,
            omega=0.0, t=0.0, rf_phi=np.pi / 2,  # sin(π/2) = 1
        )
        assert Ex == 0.0
        assert Ey == pytest.approx(5e4, rel=1e-10)

    def test_rf_kick_is_tangential_only(self):
        """At the +x gap, the cavity field is purely in the y direction."""
        Ex, Ey = rf_gap_kick(
            x=5.0, y=0.0, ring_radius=5.0, E0=1e5,
            omega=0.0, t=0.0, rf_phi=np.pi / 2,
        )
        assert Ex == 0.0
        assert Ey != 0.0


class TestFocusingField:
    """Tests for the radial restoring force."""

    def test_focusing_restores_toward_ring(self):
        """When r > R_ring, force must point radially inward."""
        ring_r = 5.0
        # Particle at r = 6 on +x axis → force should be in -x direction
        Fx, Fy = focusing_field(x=6.0, y=0.0, ring_radius=ring_r, k_focus=5e7)
        assert Fx < 0.0  # Inward
        assert abs(Fy) < 1e-10  # No y-component on x-axis

    def test_focusing_pushes_outward_when_inside(self):
        """When r < R_ring, force must point radially outward."""
        ring_r = 5.0
        Fx, Fy = focusing_field(x=4.0, y=0.0, ring_radius=ring_r, k_focus=5e7)
        assert Fx > 0.0  # Outward

    def test_focusing_zero_at_ring_radius(self):
        """No restoring force when particle is exactly on the design orbit."""
        Fx, Fy = focusing_field(x=5.0, y=0.0, ring_radius=5.0, k_focus=5e7)
        assert abs(Fx) < 1e-6
        assert abs(Fy) < 1e-6


class TestLorentzForce:
    """Tests for the Lorentz acceleration."""

    def test_lorentz_perpendicular_to_velocity(self):
        """
        Magnetic force must be perpendicular to velocity.
        For v = (v, 0) and B = Bz·ẑ → a should be in y direction only... no.
        Actually: ax = (q/m)(vy·Bz) = 0, ay = (q/m)(-vx·Bz) ≠ 0
        So for vx > 0, ay < 0 (for positive q, positive Bz).
        """
        vx, vy = 1e6, 0.0
        q, m = PROTON_CHARGE, PROTON_MASS
        ax, ay = lorentz_acceleration_2d(vx, vy, q, m, Bz=1.0)

        # F·v = ax·vx + ay·vy must be zero (magnetic force does no work)
        power = ax * vx + ay * vy
        assert abs(power) < 1e-6 * abs(ay * vx)
