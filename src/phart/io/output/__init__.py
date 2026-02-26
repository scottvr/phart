"""Output format adapters and serializers."""

from .captured_text import render_captured_text
from .dispatcher import render_renderer_output

__all__ = ["render_captured_text", "render_renderer_output"]
