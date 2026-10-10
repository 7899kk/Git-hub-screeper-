import unittest,sqlite3,pathlib
class DB(unittest.TestCase):
 def setUp(self):
  self.c=sqlite3.connect(':memory:');self.c.execute('PRAGMA foreign_keys=ON')
  for f in sorted(pathlib.Path('drizzle').glob('*.sql')):self.c.executescript(f.read_text())
  self.c.executescript("INSERT INTO platforms(id,name,host) VALUES('a','Amazon','amazon.in');INSERT INTO products(id,title,created_at) VALUES('p','Phone','2026-10-10');INSERT INTO variants VALUES('v','p','{}');INSERT INTO listings(id,product_id,variant_id,platform,url,title,created_at) VALUES('l','p','v','a','https://amazon.in/dp/1','Phone','2026-10-10');")
 def obs(self,run):self.c.execute("INSERT OR IGNORE INTO observations(id,product_id,listing_id,platform,price,observed_at,availability,verification,run_id) VALUES(?,'p','l','a',100,'2026-10-10','InStock','verified',?)",(run,run))
 def test_duplicate_run(self):
  self.obs('r1');self.obs('r1');self.assertEqual(self.c.execute('SELECT count(*) FROM observations').fetchone()[0],1)
 def test_history_preserved(self):
  self.obs('r1');self.obs('r2');self.c.execute("UPDATE listings SET state='stale'");self.assertEqual(self.c.execute('SELECT count(*) FROM observations').fetchone()[0],2)
 def test_foreign_key(self):
  with self.assertRaises(sqlite3.IntegrityError):self.c.execute("INSERT INTO watchlists VALUES('w','owner','missing','today')")
 def test_queue_lease(self):
  self.c.execute("INSERT INTO jobs(id,listing_id,due_at) VALUES('j','l','2000-01-01')");sql="UPDATE jobs SET state='running' WHERE id='j' AND state='pending'";self.assertEqual(self.c.execute(sql).rowcount,1);self.assertEqual(self.c.execute(sql).rowcount,0)
 def test_index(self):self.assertTrue(self.c.execute("SELECT name FROM sqlite_master WHERE name='history_listing_time'").fetchone())
if __name__=='__main__':unittest.main()
