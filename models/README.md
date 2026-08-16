# Production ML artifacts

Place approved `ml_edge_model.joblib` artifacts here. Model weights are deliberately not bundled because they must be trained on the broker/data feed you actually trade.

The live bridge ignores artifacts without `approved_for_live=true`.
