service DaoStrategy {
    string get_strategies(
        1:string sig,
        2:string strategy_type,
        3:string page_num,
        4:string page_limit
    );
    string run_strategy(
        1:string sig,
        2:string user_id,
        3:string strategy_instance_id,
        4:string exchange,
        5:string account_type,
        6:string strategy_type,
        7:string strategy_name,
        8:string symbol,
        9:string one_time_buy,
        10:string sms_send
    );
    string control_strategy(
        1:string sig,
        2:string user_id,
        3:string strategy_instance_id,
        4:string order
    );
    string get_strategy_instance(
        1:string sig,
        2:string user_id,
        3:string strategy_type,
        4:string status,
        5:string page_num,
        6:string page_limit
    );
    string submit_arbitrage_strategy(
        1:string sig,
        2:string user_id,
        3:string exchange_a,
        4:string exchange_b,
        5:string account_type_a,
        6:string account_type_b,
        7:string strategy_type,
        8:string symbol_a,
        9:string symbol_b,
        10:string spread_usdt,
        11:string max_trade_num,
        12:string min_trade_num,
    );
    string get_strategy_pnl(
        1:string sig,
        2:string user_id,
        3:string strategy_instance_id
    );
    string submit_conditional_strategy(
        1:string sig,
        2:string user_id,
        3:string exchange,
        4:string account_type,
        5:string strategy_type,
        6:string strategy_name,
        7:string symbol,
        8:string one_time_buy,
        9:string sms_send,
        10:string param
    );
    string get_strategy_files(
        1:string sig,
        2:string user_id,
        3:string page_num,
        4:string page_limit
    );
    string manage_strategy_file(
        1:string sig,
        2:string action,
        3:string user_id,
        4:string strategy_file_id,
        5:string file_nick_name,
        6:string file_content,
        7:string file_description
    );
    string submit_strategy_job(
        1:string sig,
        2:string strategy_name,
        3:string user_id,
        4:string begin_time,
        5:string end_time,
        6:string period,
        7:string exchange,
        8:string symbol,
        9:string exchange_2,
        10:string symbol_2,
        11:string one_time_buy,
        12:string direction,
        13:string log_record,
        14:string strategy_type,
        15:string balance_end,
        16:string balance_front,
        17:string taker_fee_ratio,
        18:string maker_fee_ratio,
        19:string strategy_file_id,
        20:string param_1_start,
        21:string param_1_end,
        22:string param_1_step,
        23:string param_2_start,
        24:string param_2_end,
        25:string param_2_step,
        26:string indicator_config
    );
    string get_strategy_jobs(
        1:string sig,
        2:string user_id,
        3:string strategy_file_id,
        4:string page_num,
        5:string page_limit
    );
    string manage_strategy_job(
        1:string sig,
        2:string action,
        3:string user_id,
        4:string strategy_job_id
    );
    string get_strategy_tasks(
        1:string sig,
        2:string user_id,
        3:string strategy_job_id,
        4:string page_num,
        5:string page_limit
    );
    string manage_strategy_task(
        1:string sig,
        2:string action,
        3:string user_id,
        4:string strategy_task_id
    );
    string get_file(
        1:string sig,
        2:string user_id,
        3:string file_name
    );
}
