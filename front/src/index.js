import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import {promise_list_ts_for_key, make_diff,timeConverter} from './App';
import Dropdown from 'react-dropdown';
import 'react-dropdown/style.css';
import ReactTable from "react-table";
import 'react-table/react-table.css'

const LocalStorageKey = "LS"
function SaveID(id) {
  var data = LoadIDs();
  data[id] = 1;
  return SaveIDs(data);
}
function LoadIDs() {
  var data = JSON.parse(localStorage.getItem(LocalStorageKey)) || {};
  return data;
}
function SaveIDs(data){
  localStorage.setItem(LocalStorageKey, JSON.stringify(data));
}
function RemoveID(id) {
  var data = LoadIDs();
  delete(data[id]);
  return SaveIDs(data);
}

function SubsribersList(props) {
  const followers = props.followers;
  if(!followers){
    return (
      <table></table>
    )
  }
  var listFollowers = function(followers, color, size){
    if(!followers) {
      return <table><tbody><tr><td>No one left</td></tr></tbody></table>
    }
    var z = []
    Object.keys(followers).map( (k) =>
              z.push({ id: followers[k]['id'], username: followers[k]['username']})

      )
      const columns = [
      {
        Header: "Img",
        accessor: "profile_pic_url",
        width: 70,
        Cell: row => (
          <a href={'https://instagram.com/'+row.original.username}><img src={row.row.profile_pic_url} width="50px"/></a>

        )
      },

      {
        Header: "username",
        accessor: "username",
        Cell: row => (
          <span>
          <a href={'https://instagram.com/'+row.original.username}>{row.value}</a>
          <br />
          {row.original.full_name}
          </span>

        )
      },
      {
        Header: "followed_by",
        accessor: "edge_followed_by.count",
        width: 100

      },
      {
        Header: "follow",
        accessor: "edge_follow.count",
        width: 100
      },
      {
        Header: "history",
        Cell: (row) => {
          var history = row.original.ihelper_user_history;
          var text_history = history.map(function(h){
                        var dt = timeConverter(h.ts);
                        return <li><span style={{color: h.val.action == 1? 'green':'red'}}>{dt} {h.val.producer}</span></li>;
                      })

          return <ul>
          {text_history}
          </ul>
        }
      }
    ];
    // var size = followers.length > 10 ? 10 : followers.length;
    console.log(size);
    return (
        <ReactTable
        data={followers}
        columns={columns}
        defaultPageSize={size}
        className="-striped -highlight"
        />
    )
}
  const deleted = followers.deleted ? followers.deleted.length : 0;
  const added = followers.created ? followers.created.length : 0;
  return (
    <div>
    {deleted} deleted, {added} added, {added-deleted} total
    <div style={{width: '60%'}}>
    <h3>Lost Followers</h3>
    {listFollowers(followers.deleted, '#aa0000', 10 )}
    </div>
    <div style={{width: '60%'}}>
    <h3>New followers</h3>
    {listFollowers(followers.created, '#00aa00', 10)}
    </div>
    </div>
  )

}


class Inhelper extends React.Component {
  constructor(props){
      super(props);
      var ids = LoadIDs();
      console.log(ids);
      this.state= {
        id: -1,
        dates: [],
        ids: ids,

      };
  }
  updateId = (event) => {
    this.setState({id: event.target.value})
  }
  updateId2 = () => {
    SaveID(this.state.id);
    promise_list_ts_for_key('followers/'+this.state.id).then(values => this.setState({dates: values, from: values[values.length-2], to: values[values.length-1]}));

  }
  updateId3 = (event) => {
    this.setState({id: event.target.innerText}, ()=>
    this.updateId2()
  );
  }
_onSelect_from = (event) => {
  this.setState({from: event})
}
_onSelect_to = (event) => {
  this.setState({to: event})
}
makeDiff = () => {
  make_diff(this.state.id, this.state.from.value, this.state.to.value).then(values=> {
    // console.log('resolved!', values);
    this.setState({ followers: values}
    )
  });

  // console.log(this.state)
}

  render() {
    return (
      <div>
      <input type="text" value={this.state.id} onChange={this.updateId}/>
      <button type="button" name="qwe" onClick={this.updateId2}>fill dates</button>
      <p>
        {
          Object.keys(this.state.ids).map((o, i) => <i key={o} onClick={this.updateId3} style={{'textDecoration': 'underline', 'paddingLeft': 10}}>{o}</i> )
        }
      </p>
      <div style={{width: '30em'}}>
        <div style={{float: 'left'}}>
          <Dropdown options={this.state.dates} onChange={this._onSelect_from} value={this.state.from} placeholder="from" />
        </div>
        <div style={{float: 'right'}}>
          <Dropdown options={this.state.dates} onChange={this._onSelect_to} value={this.state.to} placeholder="to" />
        </div>
      </div>
      <div>
        <button type="button" name="qwe" onClick={this.makeDiff}>Make diff</button>
      </div>

      <SubsribersList followers={this.state.followers} />

      </div>
    );
  }
}
ReactDOM.render(
  <Inhelper />,
  document.getElementById('root')
);
