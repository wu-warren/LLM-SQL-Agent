def test_smoke_imports():
    pass


def test_smoke_agent_loop():
    from app.agent_loop import run_agent_loop

    result = run_agent_loop("List the top 5 user ids by payment value")
    assert "status" in result

def test_smoke_join_query():
    from app.agent_loop import run_agent_loop

    result = run_agent_loop(
        "List the top 5 customers by total revenue, joining orders and order_payments")
    
    assert result.get("status") == "success"

def test_smoke_nonexistent_column_query():
    from app.agent_loop import run_agent_loop

    result = run_agent_loop("select data from a nonexistent column")
    
    assert "status" in result

def test_smoke_gibberish_query():
    from app.agent_loop import run_agent_loop

    result = run_agent_loop("asdfasdfasdf asdf asdf")
    
    assert "status" in result