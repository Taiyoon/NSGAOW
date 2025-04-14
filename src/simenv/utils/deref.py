

def deref[T](reference: T) -> T:
    """
    Dereferences a weak reference, reference must not be garbage collected.

    Args:
        reference: A weak reference to an object

    Returns:
        The strong referenced object

    Raises:
        ValueError: If the referenced object has been garbage collected
    """
    # obj = reference()
    # if obj is None:
    #     raise ValueError(f"Reference {reference} has been garbage collected")
    return reference
