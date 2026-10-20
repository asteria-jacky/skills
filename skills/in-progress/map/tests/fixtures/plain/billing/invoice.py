from shipping.parcel import Parcel


class Invoice:
    def __init__(self, parcel: Parcel):
        self.parcel = parcel
