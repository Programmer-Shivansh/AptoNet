module VPORT_MANAGEMENT::VPortManagement {
    use std::signer;

    struct VPort has key, store {
        owner: address,
        name: vector<u8>,
    }

    // Register a new VPort
    public entry fun register_vport(account: &signer, name: vector<u8>) {
        let address = signer::address_of(account);
        let vport = VPort {
            owner: address,
            name,
        };
        move_to(account, vport);
    }

    // Authenticate a VPort (simple ownership check)
    public fun authenticate_vport(vport_address: address, account: &signer): bool acquires VPort {
        let caller = signer::address_of(account);
        assert!(exists<VPort>(vport_address), 1);
        let vport = borrow_global<VPort>(vport_address);
        vport.owner == caller
    }

    // Update VPort name
    public entry fun update_vport_name(account: &signer, new_name: vector<u8>) acquires VPort {
        let address = signer::address_of(account);
        assert!(exists<VPort>(address), 2);
        let vport = borrow_global_mut<VPort>(address);
        vport.name = new_name;
    }

    // Delete VPort
    public entry fun delete_vport(account: &signer) acquires VPort {
        let address = signer::address_of(account);
        assert!(exists<VPort>(address), 3);
        let VPort { owner: _, name: _ } = move_from<VPort>(address);
    }

    // Get VPort info
    public fun get_vport_info(vport_address: address): (address, vector<u8>) acquires VPort {
        assert!(exists<VPort>(vport_address), 4);
        let vport = borrow_global<VPort>(vport_address);
        (vport.owner, vport.name)
    }
}