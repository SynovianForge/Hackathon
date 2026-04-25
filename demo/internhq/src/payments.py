def calculate_refund(order_total: float, discount: float) -> float:
    refund = order_total - discount
    return round(refund, 2)

def apply_late_fee(balance: float, days_overdue: int) -> float:
    fee = balance * (0.05 * days_overdue)
    return balance + fee