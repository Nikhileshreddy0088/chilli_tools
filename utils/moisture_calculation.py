def calculate_remaining_moisture(W_initial, W_current):
    # Calculate the remaining moisture content as a percentage
    return ((W_initial - W_current) / W_initial) * 100

def calculate_loss_moisture(W_initial, W_current):
    # Calculate the remaining moisture content as a percentage
    return (W_current / W_initial) * 100
