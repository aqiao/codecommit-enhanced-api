-- team is reserved word in sqlite

DROP TABLE IF EXISTS team;
DROP TABLE IF EXISTS project;
DROP TABLE IF EXISTS repo;
DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS policy;
DROP TABLE IF EXISTS team_member;
DROP TABLE IF EXISTS team_project;
DROP TABLE IF EXISTS team_policy;


CREATE TABLE project(
    id integer primary key autoincrement,
    project_name unique not null,
    status text default "正常",
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    owner_id integer,
    owner_name text,
    operator integer
);

CREATE TABLE team(
    id integer primary key autoincrement,
    team_name text unique not null,
    status text default "正常",
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    leader_id integer,
    leader_name text,
    operator integer,
    aws_arn text
    -- Commented below restriction in case there is not strong relation between project and team
    -- foreign key(project_id) references project(id)
);

CREATE TABLE repo(
    id integer primary key autoincrement,
    -- DO NOT set project_id as foreign key to support batch import from GitHub
    project_id integer,
    project_name text,
    owner_id integer,
    owner_name text,
    repo_name unique not null,
    description text,
    status text default "正常",
    origin_link text,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    operator integer,
    aws_arn text,
    clone_url_https text,
    clone_url_ssh text
);

CREATE TABLE user(
    id integer primary key autoincrement,
    user_name unique not null,
    email unique not null,
    password varchar(500) not null,
    status text default "正常",
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    operator integer,
    aws_arn text,
    ak text,
    sk text
);

CREATE TABLE team_member(
    user_name text not null,
    team_name text not null,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    operator integer,
    primary key(user_name,team_name)
);

CREATE TABLE team_project(
    team_id integer not null,
    team_name text,
    project_id integer not null,
    project_name text,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    operator integer,
    primary key(team_id,project_id)
);

CREATE TABLE policy(
    policy_name text not null,
    detail text,
    status text default "正常",
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    operator integer,
    aws_arn text,
    primary key(policy_name)
);

CREATE TABLE team_policy(
    team_name text not null,
    policy_arn text not null
);

-- initialize data
insert into policy (policy_name, operator, aws_arn) values ('AWSCodeCommitFullAccess' ,1, 'arn:aws-cn:iam::aws:policy/AWSCodeCommitFullAccess');
insert into policy (policy_name, operator, aws_arn) values ('AWSCodeCommitPowerUser' ,1, 'arn:aws-cn:iam::aws:policy/AWSCodeCommitPowerUser');
insert into policy (policy_name, operator, aws_arn) values ('AWSCodeCommitReadOnly' ,1, 'arn:aws-cn:iam::aws:policy/AWSCodeCommitReadOnly');
