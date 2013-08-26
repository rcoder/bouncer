drop table if exists urls;

create table urls (
  slug text,
  full_url text,
  clicks int default 0,
  ctime timestamp default current_timestamp,
  atime timestamp default current_timestamp
);
