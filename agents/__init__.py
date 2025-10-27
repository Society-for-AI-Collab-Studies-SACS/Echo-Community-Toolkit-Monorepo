"""Agent packages for the VesselOS monorepo."""

from pkgutil import extend_path

# Allow stitched packages from Echo-Community-Toolkit/agents.
__path__ = extend_path(__path__, __name__)
