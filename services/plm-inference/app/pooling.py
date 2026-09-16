"""
Mean-pooling over valid residue embeddings.

ESM2 tokenizers add one beginning-of-sequence special token at position 0 and one
end-of-sequence special token immediately after the last residue. Both must be
excluded from pooling, in addition to any right-padding, so the returned vector
reflects residues only — never the masked-language-model logits, and never a
representation contaminated by special-token or padding vectors.
"""
from typing import Any


def mean_pool_residues(hidden_states: Any, attention_mask: Any) -> Any:
    """
    hidden_states: (batch, seq_len, hidden_dim) tensor, typically output.last_hidden_state
    attention_mask: (batch, seq_len) tensor from the tokenizer (1 for real tokens
        including special tokens, 0 for padding)

    Returns: (batch, hidden_dim) tensor of per-sequence mean-pooled residue embeddings.
    """
    residue_mask = attention_mask.clone()
    # Exclude the beginning-of-sequence special token (position 0) for every row.
    residue_mask[:, 0] = 0
    # Exclude the end-of-sequence special token: the last position where
    # attention_mask == 1 for that row (works regardless of right-padding length).
    lengths = attention_mask.sum(dim=1)
    for row, length in enumerate(lengths.tolist()):
        end_index = int(length) - 1
        if end_index >= 0:
            residue_mask[row, end_index] = 0

    mask = residue_mask.unsqueeze(-1).to(hidden_states.dtype)
    summed = (hidden_states * mask).sum(dim=1)
    counts = mask.sum(dim=1).clamp(min=1)
    return summed / counts
