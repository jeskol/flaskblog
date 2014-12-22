drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  title text not null,
  text text not null,
  created datetime default current_timestamp,
  modified datetime default current_timestamp
);
