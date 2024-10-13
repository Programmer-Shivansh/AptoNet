module MAC_TABLE::MACTable {
    use std::signer;
    use aptos_framework::table::{Self, Table};
    use aptos_framework::event;
    use aptos_framework::account;

    struct MACTable has key {
        entries: Table<vector<u8>, address>,
        count: u64,
    }

    struct MACEntryAddedEvent has drop, store {
        mac_address: vector<u8>,
        vport: address,
    }

    struct MACEntryRemovedEvent has drop, store {
        mac_address: vector<u8>,
    }

    struct EventHandle has key {
        add_events: event::EventHandle<MACEntryAddedEvent>,
        remove_events: event::EventHandle<MACEntryRemovedEvent>,
    }

    const E_NOT_INITIALIZED: u64 = 1;
    const E_ALREADY_INITIALIZED: u64 = 2;
    const E_NOT_AUTHORIZED: u64 = 3;
    const E_MAC_NOT_FOUND: u64 = 4;

    public fun initialize(account: &signer) {
        let addr = signer::address_of(account);
        assert!(!exists<MACTable>(addr), E_ALREADY_INITIALIZED);
        
        move_to(account, MACTable {
            entries: table::new(),
            count: 0,
        });
        
        move_to(account, EventHandle {
            add_events: account::new_event_handle<MACEntryAddedEvent>(account),
            remove_events: account::new_event_handle<MACEntryRemovedEvent>(account),
        });
    }

    public entry fun upsert_mac(account: &signer, mac: vector<u8>, vport: address) acquires MACTable, EventHandle {
        let addr = signer::address_of(account);
        assert!(exists<MACTable>(addr), E_NOT_INITIALIZED);
        
        let mac_table = borrow_global_mut<MACTable>(addr);
        if (!table::contains(&mac_table.entries, mac)) {
            mac_table.count = mac_table.count + 1;
        };
        table::upsert(&mut mac_table.entries, mac, vport);

        let event_handle = borrow_global_mut<EventHandle>(addr);
        event::emit_event(&mut event_handle.add_events, MACEntryAddedEvent {
            mac_address: mac,
            vport,
        });
    }

    public fun lookup_mac(account: &signer, mac: vector<u8>): address acquires MACTable {
        let addr = signer::address_of(account);
        assert!(exists<MACTable>(addr), E_NOT_INITIALIZED);
        
        let mac_table = borrow_global<MACTable>(addr);
        assert!(table::contains(&mac_table.entries, mac), E_MAC_NOT_FOUND);
        *table::borrow(&mac_table.entries, mac)
    }

    public entry fun remove_mac(account: &signer, mac: vector<u8>) acquires MACTable, EventHandle {
        let addr = signer::address_of(account);
        assert!(exists<MACTable>(addr), E_NOT_INITIALIZED);
        
        let mac_table = borrow_global_mut<MACTable>(addr);
        assert!(table::contains(&mac_table.entries, mac), E_MAC_NOT_FOUND);
        table::remove(&mut mac_table.entries, mac);
        mac_table.count = mac_table.count - 1;

        let event_handle = borrow_global_mut<EventHandle>(addr);
        event::emit_event(&mut event_handle.remove_events, MACEntryRemovedEvent {
            mac_address: mac,
        });
    }

    public fun get_vport_count(account: &signer): u64 acquires MACTable {
        let addr = signer::address_of(account);
        assert!(exists<MACTable>(addr), E_NOT_INITIALIZED);
        
        let mac_table = borrow_global<MACTable>(addr);
        mac_table.count
    }
}