import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import { promise_list_ts_for_key, make_diff, getInfoById, timeConverter } from './App';
import Dropdown from 'react-dropdown';
import 'react-dropdown/style.css';
import SubsribersList from "./subscribersList";

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
function SaveIDs(data) {
  localStorage.setItem(LocalStorageKey, JSON.stringify(data));
}
function RemoveID(id) {
  var data = LoadIDs();
  delete (data[id]);
  return SaveIDs(data);
}



class Inhelper extends React.Component {
  constructor(props) {
    super(props);
    var ids = LoadIDs();
    console.log(ids);
    this.state = {
      id: -1,
      dates: [],
      ids: ids,
      followers: {},
    };
  }
  updateId = (event) => {
    this.setState({ id: event.target.value })
  }
  updateId2 = () => {
    SaveID(this.state.id);
    promise_list_ts_for_key('followers/' + this.state.id).then(values => {
      this.setState({
        dates: values,
        from: values[values.length - 2],
        to: values[values.length - 1]
      });
    });
  }
  updateId3 = (event) => {
    this.setState({ id: event.target.innerText }, () =>
      this.updateId2()
    );
  }
  _onSelect_from = (event) => {
    this.setState({
      from: event
    });
  }
  _onSelect_to = (event) => {
    this.setState({
      to: event
    });
  }
  makeDiff = () => {
    make_diff(this.state.id, this.state.from.value, this.state.to.value).then(values => {
      this.setState({ followers: values });
    });

  }

  render() {
    return (
      <div>
        <input type="text" value={this.state.id} onChange={this.updateId} />
        <button type="button" name="qwe" onClick={this.updateId2}>fill dates</button>
        <p>
          {
            Object.keys(this.state.ids).map((o, i) => <i key={o} onClick={this.updateId3} style={{ 'textDecoration': 'underline', 'paddingLeft': 10 }}>{o}</i>)
          }
        </p>
        <div style={{ width: '30em' }}>
          <div style={{ float: 'left' }}>
            <Dropdown options={this.state.dates} onChange={this._onSelect_from} value={this.state.from} placeholder="from" />
          </div>
          <div style={{ float: 'right' }}>
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
