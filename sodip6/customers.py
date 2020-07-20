
class Customer:
    def __init__(self, id,name,addr,gw,prio):
        self.id = id
        self.customer_name = name
        self.customer_address = addr
        self.customer_gateway = gw
        self.customer_priority = prio

    def set_customer_gateway(self, gateway):
        self.customer_gateway = gateway

    def get_customer_gateway(self):
        return self.customer_gateway

    def set_customer_priority(self, priority):
        self.customer_priority = priority

    def get_customer_priority(self):
        return self.customer_priority

    def get_customer_details(self):
        custdetails={   'id': self.id,
                        'custname' : self.customer_name,
                        'custaddress' : self.customer_address,
                        'custgateway' : self.customer_gateway,
                        'custpriority' : self.customer_priority
                    }
        return custdetails


class CustomerDetails:
    def __init__(self):
        self.cust_dict = {}
        self.cust_no = 0

    def add_customer(self, id,name,addr,gw,prio):
        self.cust_no += 1
        new_customer = Customer(id,name,addr,gw,prio)
        self.cust_dict[id] = new_customer
        return new_customer

    def get_customer(self, id):
        if id in self.cust_dict:
            return self.cust_dict[id]
        else:
            return None


