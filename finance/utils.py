def apply_sponsorship(amount, sponsorship):
    """
    Takes original amount and sponsorship object
    Returns discounted amount
    """
    if not sponsorship:
        return amount

    if sponsorship.sponsorship_type == "full":
        return 0

    if sponsorship.sponsorship_type == "partial":
        discount = (sponsorship.percentage_covered / 100) * amount
        return amount - discount

    return amount
