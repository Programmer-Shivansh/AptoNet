module VPORT_MANAGEMENT::VPortManagement {
    use std::signer;
    use std::vector;

    struct VPort has store {
        owner: address,
        name: vector<u8>,
    }

    // Register a new VPort
    public fun register_vport(account: &signer, name: vector<u8>) {
        let address = signer::address_of(account);
        let vport = VPort {
            owner: address,
            name,
        };
        move_to(account, vport);
    }

    // Authenticate a VPort (simple ownership check)
    public fun authenticate_vport(vport_address: address, account: &signer) {
        let caller = signer::address_of(account);
        let vport = borrow_global<VPort>(vport_address);
        assert!(vport.owner == caller, 1, "Authentication failed");
    }

    // Additional functions like update_vport, delete_vport can be added here
}
