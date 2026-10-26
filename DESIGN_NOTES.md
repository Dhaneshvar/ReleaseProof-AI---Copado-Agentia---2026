# ReleaseProof design direction

The product uses a simple release-console language: graphite surfaces, one acid-green action color, warm neutral text, thin rules, compact labels and direct evidence states. Avoid generic AI-dashboard tropes such as purple-blue gradients, floating glass cards, excessive glow, decorative 3D art and unexplained confidence meters.

## Reference set

These are inspiration sources, not copy targets:

- [Minimal Gallery](https://minimal.gallery/) for restraint and information hierarchy.
- [Refero Styles](https://styles.refero.design/) for readable product typography and system thinking.
- [shadcn/ui](https://ui.shadcn.com/) for composable, accessible interaction patterns.
- [Component Gallery](https://component.gallery/) for comparing interaction patterns before inventing one.
- [Motion Primitives](https://motion-primitives.com/) and [Kinetics](https://kinetics.colorion.co/) for restrained motion only where it explains state.
- [21st.dev](https://21st.dev/) for implementation inspiration when a component genuinely needs a richer interaction.

## Rules for future work

1. Every primary button must perform a real action or open a useful state.
2. Evidence cards must be drillable; no decorative metrics without source detail.
3. Keep the palette mostly neutral. Reserve acid green for verified/actionable states and amber for risk.
4. Prefer borders, spacing and type scale over gradients and shadows.
5. Motion should show progress, loading or transition—not decoration.
6. Keep Copado and Agentia visible as the execution system, while ReleaseProof explains the evidence.

