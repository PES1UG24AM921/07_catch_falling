"""
collision: figures out whether a falling object is within the basket.
"""

# Spawn code uses y=-14, which suggests objects are ~14px in radius with y
# as their centre. Used only if FallingObject has no `radius` attribute.
DEFAULT_OBJECT_RADIUS = 14


def is_caught(basket_rect, obj):
    radius = getattr(obj, "radius", DEFAULT_OBJECT_RADIUS)
    obj_top = obj.y - radius
    obj_bottom = obj.y + radius

    # Horizontal: object is between the basket's left and right edges.
    within_x = basket_rect.left <= obj.x <= basket_rect.right

    # Vertical: object's bottom has reached the basket's top, and the
    # object hasn't gone past the bottom of the basket.
    reached_basket = obj_bottom >= basket_rect.top
    not_past_basket = obj_top <= basket_rect.bottom

    return within_x and reached_basket and not_past_basket