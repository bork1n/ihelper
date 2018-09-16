//var DynamoDB = require('dynamodb')
var AWS = require('aws-sdk')
const zlib = require('zlib');
// Initialize the Amazon Cognito credentials provider

console.log(process.env.REACT_APP_AWS_REGION,process.env.REACT_APP_IDENTITYPOOLID);
AWS.config.region = process.env.REACT_APP_AWS_REGION; // Region
AWS.config.credentials = new AWS.CognitoIdentityCredentials({
  IdentityPoolId: process.env.REACT_APP_IDENTITYPOOLID,
});

var docClient = new AWS.DynamoDB.DocumentClient();
var s3 = new AWS.S3();

const s3bucket ='ihelper';
const ddbtable = 'ihelper';


function fetchData(key, ts, limit, cb) {
  // console.log("running with ", key);
  var params = {
    TableName: ddbtable,
    KeyConditionExpression: "#yr = :yyyy",
    ExpressionAttributeNames: {
      "#yr": "key"
    },
    ExpressionAttributeValues: {
      ":yyyy": key
    }
  };
  if (limit) {
    params['Limit'] = limit;
  }
  if (ts) {
    params['KeyConditionExpression'] = "#yr = :yyyy and #ts = :ts";
    params['ExpressionAttributeNames']['#ts'] = 'ts';
    params['ExpressionAttributeValues'][':ts'] = ts;
  }
  // console.log(params);
  var res = [];
  docClient.query(params, function(err, data) {
    if (err) {
      console.error("Unable to query. Error:", JSON.stringify(err, null, 2));
    } else {
      data.Items.forEach(function(item) {
        var promise = new Promise(function(resolve, reject) {

        if (typeof(item.val.startsWith) == 'function' && item.val.startsWith(key)) {
          console.log('s3!');
          var res_value = 0;
          s3.getObject({
            Bucket: s3bucket,
            Key: item.val
          }, (error, data) => {
            if (error != null) {
              console.log(error);
            } else {
              res_value = JSON.parse(data.Body.toString());
              resolve({
                ts: item.ts,
                val: res_value
              });
            }
          })
        } else {
          zlib.unzip(item.val, (err, buffer) => {
            if (!err) {
              var str = buffer.toString();
              res_value = JSON.parse(str);
              resolve({
                ts: item.ts,
                val: res_value
              });
            } else {
              console.log(err);
              // handle error
            }
          });
          //console.log(item.ts);
        }
      });
        res.push(promise)
      });

    }
  if(limit == 1){
    if(res[0]) {
    res[0].then((value)=> {
          cb(value.val);
    });
  } else {
    console.log('calling cb after 404 for ', key);
    cb({});
  }
  } else {
    Promise.all(res).then((values)=>{
    cb(values);
  });
  }
});

}

function promise_fetch(key, ts) {
  return new Promise((resolve, reject) => {
    if (!ts) {
      ts = 0;
    }
    fetchData(key, ts, 1, function(a) {
      //console.log(a);
      resolve(a);
    });
  });
}


var deepDiffMapper = function() {
  return {
    VALUE_CREATED: 'created',
    VALUE_UPDATED: 'updated',
    VALUE_DELETED: 'deleted',
    VALUE_UNCHANGED: 'unchanged',
    map: function(obj1, obj2) {
      if (this.isFunction(obj1) || this.isFunction(obj2)) {
        throw 'Invalid argument. Function given, object expected.';
      }
      if (this.isValue(obj1) || this.isValue(obj2)) {
        return {
          type: this.compareValues(obj1, obj2),
          data: (obj1 === undefined) ? obj2 : obj1
        };
      }

      var diff = {};
      for (var key in obj1) {
        if (this.isFunction(obj1[key])) {
          continue;
        }

        var value2 = undefined;
        if ('undefined' != typeof(obj2[key])) {
          value2 = obj2[key];
        }

        diff[key] = this.map(obj1[key], value2);
      }
      for (var key in obj2) {
        if (this.isFunction(obj2[key]) || ('undefined' != typeof(diff[key]))) {
          continue;
        }

        diff[key] = this.map(undefined, obj2[key]);
      }


      return diff;

    },
    compareValues: function(value1, value2) {
      if (value1 === value2) {
        return this.VALUE_UNCHANGED;
      }
      if (this.isDate(value1) && this.isDate(value2) && value1.getTime() === value2.getTime()) {
        return this.VALUE_UNCHANGED;
      }
      if ('undefined' == typeof(value1)) {
        return this.VALUE_CREATED;
      }
      if ('undefined' == typeof(value2)) {
        return this.VALUE_DELETED;
      }

      return this.VALUE_UPDATED;
    },
    isFunction: function(obj) {
      return {}.toString.apply(obj) === '[object Function]';
    },
    isArray: function(obj) {
      return {}.toString.apply(obj) === '[object Array]';
    },
    isDate: function(obj) {
      return {}.toString.apply(obj) === '[object Date]';
    },
    isObject: function(obj) {
      return {}.toString.apply(obj) === '[object Object]';
    },
    isValue: function(obj) {
      return !this.isObject(obj) && !this.isArray(obj);
    }
  }
}();

function diff_to_dict(v1, v2) {
  var r = deepDiffMapper.map(v1, v2);
  // var res = {};
  var promises = [];
  // var idx = 0;
  for (var el in r) {
    var item = r[el];
    if (typeof(item['type']) == 'undefined') {
      // XXX: shiuld'n be in dicct at all
      continue;
    }
    // idx = res[item['type']].length;
    // res[item['type']].push(item['data']);
    //XXX: instead, push whole subscriber data into snapshot
    function make_prom(promises, item) {
      return new Promise((resolve, reject) => {
        fetchData('profiles/' + item['data']['id'], 0, 1, (data) => {
          var res;
          if(JSON.stringify(data) === '{}'){
            data = item['data'];
            data['edge_followed_by'] = {};
            data['edge_followed_by']['count'] = -1;
            data['edge_follow'] = {};
            data['edge_follow']['count'] = -1;
            data['ihelper_user_history'] = [];
          }
            fetchData('follows/' + item['data']['id'], 0, 1000, (data2) => {
              data['ihelper_user_history']=data2;
              res = [item['type'], data];
              console.log(res);
              resolve(res);
            });
        })
      });

    }
    var promise = make_prom(promises, item);


    promises.push(promise);
  }
  // console.log(promises);
  return Promise.all(promises).then(values => {
    var res = {};
    for (var idx in values) {
      var item = values[idx];
      // var item = r[el];
      if (typeof(res[item[0]]) == 'undefined') {
        res[item[0]] = [];
      }
      res[item[0]].push(item[1])
    }
    return res;
  });
}


function make_diff(user_id, ts1, ts2) {
  if (ts1 > ts2) {
    console.log("ts1<ts2@");
    return Promise.reject('ts1<ts2');
  }
  return Promise.all([
    promise_fetch('followers/' + user_id, ts1),
    promise_fetch('followers/' + user_id, ts2)
  ]).then(values => diff_to_dict(values[0], values[1]));
}




function timeConverter(UNIX_timestamp) {
  var a = new Date(UNIX_timestamp * 1000);
  var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  var year = a.getFullYear();
  var month = months[a.getMonth()];
  var date = a.getDate();
  var hour = a.getHours();
  var min = a.getMinutes();
  var sec = a.getSeconds();
  var time = date + ' ' + month + ' ' + year + ' ' + hour + ':' + min;
  return time;
}
/*
XXX: should be joined with fetchData
*/
function list_ts_for_key(key, ts, cb) {
  var params = {
    TableName: ddbtable,
    KeyConditionExpression: "#yr = :yyyy",
    ExpressionAttributeNames: {
      "#yr": "key"
    },
    ExpressionAttributeValues: {
      ":yyyy": key
    },
  };
  //console.log(params);
  docClient.query(params, function(err, data) {
    if (err) {
      console.error("Unable to query. Error:", JSON.stringify(err, null, 2));
    } else {
      var res = []
      data.Items.forEach(function(item) {
        res.push({
          value: item.ts,
          label: timeConverter(item.ts)
        })
        // res[item.ts] = timeConverter(item.ts);
      });
      cb(res);
    }
  });
}

function promise_list_ts_for_key(key, ts) {
  return new Promise((resolve, reject) => {
    if (!ts) {
      ts = 0;
    }
    list_ts_for_key(key, ts, function(a) {
      //console.log(a);
      resolve(a);
    });
  });
}

export default promise_list_ts_for_key;
export {
  promise_list_ts_for_key,
  make_diff,
  timeConverter
};
