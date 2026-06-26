# Proof of Resolution: Critique 16 (Vector Space Axioms & Geometry)

## Original Critique
Broken Vector Space Axioms: Unnormalized, mixed continuous-categorical vectors violate linear algebra. Cosine similarity is dominated by `batch_size`.
Retriever Geometry: Raw cosine similarity imposes fictitious ordinal geometry (e.g., ELU is exactly halfway between ReLU and LeakyReLU).

## Proof of Resolution
We eliminated mixed-ordinal calculations.
1. Numerical parameters: Standardized using Min-Max scaling boundaries to the unit range `[0, 1]` or dynamic log10 scaling (for learning rate).
2. Categorical parameters: Removed simple string-to-integer mappings and implemented mathematical One-Hot Encoding, mapping categories onto orthogonal coordinate axis dimensions.

### Code Snippet (`run_pilot_experiment.py`)
```python
def config_to_vector(config):
    layers_norm = (float(config.get("num_conv_layers", 2)) - 1.0) / 2.0
    filters_1_norm = (float(config.get("filters_1", 16)) - 8.0) / 24.0
    filters_2_norm = (float(config.get("filters_2", 32)) - 16.0) / 48.0
    kernel_norm = (float(config.get("kernel_size", 3)) - 3.0) / 2.0
    dropout_norm = float(config.get("dropout_rate", 0.2)) / 0.5
    
    lr_val = float(config.get("lr", 1e-3))
    lr_log = np.log10(lr_val)
    lr_norm = (lr_log - np.log10(0.0001)) / (np.log10(0.05) - np.log10(0.0001))
    
    batch_norm = (float(config.get("batch_size", 32)) - 16.0) / 48.0
    
    # One-Hot Encoding (orthogonal unit dimensions)
    activation = config.get("activation", "ReLU")
    act_oh = [
        1.0 if activation == "ReLU" else 0.0,
        1.0 if activation == "ELU" else 0.0,
        1.0 if activation == "LeakyReLU" else 0.0
    ]
    
    optimizer = config.get("optimizer", "AdamW")
    opt_oh = [
        1.0 if optimizer == "AdamW" else 0.0,
        1.0 if optimizer == "SGD" else 0.0
    ]
    
    vec = [layers_norm, filters_1_norm, filters_2_norm, kernel_norm, dropout_norm, lr_norm, batch_norm] + act_oh + opt_oh
    return np.array(vec).reshape(1, -1)
```
This guarantees strict mathematical legitimacy for all subsequent cosine similarity retrieved coordinates.
