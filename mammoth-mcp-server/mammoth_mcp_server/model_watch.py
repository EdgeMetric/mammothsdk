"""Whether the model is still waiting on what a widget in the chat is also watching.

A widget cannot start a turn. Its `ui/message` lands in Claude's message box, for
the person to send, and answering a tool with `waiting` lets the model end its
turn. So the model keeps polling while the person works, and carries on by itself
when the poll comes back finished.

That leaves two watchers. If the widget hands back too, a stale "carry on" sits in
the message box after the model has already moved on. So the model's calls leave a
note here, and the widget hands back only when the model has left.

A note of its own, not a field on the upload ticket: a model's poll writing the
ticket back could undo the write that spends it.
"""

import time

from .consts import UPLOAD_SECONDS, ModelWatchFields
from .store import forget, recall, remember


async def model_is_polling(key: str) -> None:
    """Note that the model is waiting on this upload or connection."""
    await remember(
        ModelWatchFields.KIND, key, {ModelWatchFields.POLLED_AT: time.time()}, UPLOAD_SECONDS
    )


async def model_was_told(key: str) -> None:
    """Note that the model has the result, so the widget has nothing to hand back."""
    await remember(ModelWatchFields.KIND, key, {ModelWatchFields.TOLD: True}, UPLOAD_SECONDS)


async def model_gave_up(key: str) -> None:
    """Drop the note: the model was told to stop, so the widget should not wait for it."""
    await forget(ModelWatchFields.KIND, key)


async def model_state(key: str) -> str:
    """Where the model stands, for the widget.

    Args:
        key: The upload id or watch id the model polls with.

    Returns:
        `told` when the model has the result, `watching` when it polled recently
        enough to be between calls, and `gone` otherwise.
    """
    note = await recall(ModelWatchFields.KIND, key)
    if note is None:
        return ModelWatchFields.GONE
    if note.get(ModelWatchFields.TOLD):
        return ModelWatchFields.TOLD
    since = time.time() - float(note[ModelWatchFields.POLLED_AT])
    if since < ModelWatchFields.GAP_SECONDS:
        return ModelWatchFields.WATCHING
    return ModelWatchFields.GONE
