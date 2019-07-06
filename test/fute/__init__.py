from test_helpers.testcasebase import TEST_EXEC_TIMES

def teardown_package():
	exec_times = sorted(TEST_EXEC_TIMES, key=lambda item: item[1], reverse=True)[:10]
	if exec_times:
		print "\nTop 10 slowest tests"
		for id, exec_time in exec_times:
			print "  {:.3f} secs".format(exec_time), "::", id
